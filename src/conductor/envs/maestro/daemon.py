import asyncio
import logging
import pathlib
import time
from typing import Any, Dict

from conductor.config import MAESTRO_WORKSPACE_LOCATION, MAESTRO_WORKSPACE_NAME_FORMAT
from conductor.context import Context
from conductor.envs.maestro.interface import (
    MaestroInterface,
    ExecuteTaskResponse,
    ExecuteTaskType,
)
from conductor.errors import InternalError
from conductor.execution.executor import Executor
from conductor.execution.operation_state import OperationState
from conductor.execution.ops.run_task_executable import RunTaskExecutable
from conductor.execution.plan import ExecutionPlan
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.run import RunCommand, RunExperiment

logger = logging.getLogger(__name__)


class Maestro(MaestroInterface):
    """
    Maestro is Conductor's remote daemon. It runs within a user-defined
    environment and executes tasks when requested by the main Conductor process.
    """

    def __init__(self, maestro_root: pathlib.Path) -> None:
        self._maestro_root = maestro_root
        # Stores the contexts for each workspace. This allows for context reuse.
        self._contexts: Dict[pathlib.Path, Context] = {}

    async def unpack_bundle(self, bundle_path: pathlib.Path) -> str:
        bundle_name = bundle_path.stem
        workspace_name = MAESTRO_WORKSPACE_NAME_FORMAT.format(
            name=bundle_name, timestamp=str(int(time.time()))
        )
        abs_workspace_path = (
            self._maestro_root / MAESTRO_WORKSPACE_LOCATION / workspace_name
        )
        abs_workspace_path.mkdir(parents=True, exist_ok=True)
        abs_bundle_path = self._maestro_root / bundle_path
        # N.B. Good practice to use async versions here, but we intend to have
        # only one caller.
        clone_args = ["git", "clone", str(abs_bundle_path), str(abs_workspace_path)]
        logger.debug("Running args: %s", str(clone_args))
        process = await asyncio.create_subprocess_exec(*clone_args)
        await process.wait()
        if process.returncode != 0:
            raise RuntimeError("Failed to unpack the bundle.")
        return workspace_name

    async def execute_task(
        self,
        workspace_name: str,
        project_root: pathlib.Path,
        task_identifier: TaskIdentifier,
        dep_versions: Dict[TaskIdentifier, Version],
        execute_task_type: ExecuteTaskType,
    ) -> ExecuteTaskResponse:
        workspace_path = (
            self._maestro_root / MAESTRO_WORKSPACE_LOCATION / workspace_name
        )
        if not workspace_path.exists():
            raise InternalError(details=f"Workspace {workspace_name} does not exist.")

        full_project_root = workspace_path / project_root
        if not full_project_root.exists():
            raise InternalError(
                details=f"Project root {project_root} does not exist in workspace {workspace_name}."
            )

        start_timestamp = int(time.time())

        # 1. Load and parse this task's dependencies.
        ctx = self._get_context(full_project_root)
        ctx.task_index.load_transitive_closure(task_identifier)

        # 2. Assemble the paths to the task's dependencies' outputs.
        task_to_run = ctx.task_index.get_task(task_identifier)
        if not (
            isinstance(task_to_run, RunExperiment)
            or isinstance(task_to_run, RunCommand)
        ):
            raise InternalError(
                details=f"Task {task_identifier} is not a run_experiment() or run_command() task."
            )

        deps_output_paths = []
        for dep_id in task_to_run.deps:
            dep_task = ctx.task_index.get_task(dep_id)
            if dep_id in dep_versions:
                version = dep_versions[dep_id]
            else:
                version = None
            output_path = dep_task.get_specific_output_path(ctx, version)
            if output_path is not None:
                deps_output_paths.append(output_path)

        # 3. Create the task execution operation.
        kwargs: Dict[str, Any] = {
            "initial_state": OperationState.QUEUED,
            "task": task_to_run,
            "identifier": task_identifier,
            "run": task_to_run.raw_run,
            "args": task_to_run.args,
            "options": task_to_run.options,
            "working_path": task_to_run.get_working_path(ctx),
            "deps_output_paths": deps_output_paths,
            "parallelizable": task_to_run.parallelizable,
        }

        if execute_task_type == ExecuteTaskType.RunExperiment:
            assert isinstance(task_to_run, RunExperiment)
            # We need it to be versioned.
            exp_version = task_to_run.create_new_version(ctx)
            output_path = task_to_run.get_output_path(ctx)
            assert output_path is not None
            kwargs["record_output"] = True
            kwargs["version_to_record"] = exp_version
            kwargs["serialize_args_options"] = True
            kwargs["output_path"] = output_path
        elif execute_task_type == ExecuteTaskType.RunCommand:
            output_path = task_to_run.get_output_path(ctx)
            assert output_path is not None
            kwargs["record_output"] = False
            kwargs["version_to_record"] = None
            kwargs["serialize_args_options"] = False
            kwargs["output_path"] = output_path
        else:
            raise InternalError(
                details=f"Unsupported task type {str(execute_task_type)}."
            )

        op = RunTaskExecutable(**kwargs)  # pylint: disable=missing-kwoa

        # 4. Run the task.
        plan = ExecutionPlan(
            task_to_run=task_to_run,
            all_ops=[op],
            initial_ops=[op],
            cached_tasks=[],
            num_tasks_to_run=1,
        )
        executor = Executor(execution_slots=1, silent=True)
        executor.run_plan(plan, ctx)

        end_timestamp = int(time.time())
        return ExecuteTaskResponse(
            start_timestamp=start_timestamp, end_timestamp=end_timestamp
        )

    async def shutdown(self, key: str) -> str:
        logger.info("Received shutdown message with key %s", key)
        loop = asyncio.get_running_loop()
        loop.create_task(_orchestrate_shutdown())
        return "OK"

    def _get_context(self, full_project_root: pathlib.Path) -> Context:
        if full_project_root not in self._contexts:
            self._contexts[full_project_root] = Context(full_project_root)
        return self._contexts[full_project_root]


async def _orchestrate_shutdown() -> None:
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
