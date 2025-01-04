import pathlib
from typing import Dict, Optional

from conductor.context import Context
from conductor.errors import MissingEnvSupport, EnvsRequireGit, InternalError
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.ops.operation import Operation
from conductor.execution.operation_state import OperationState
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType
from conductor.task_types.run import RunCommand, RunExperiment


class RunRemoteTask(Operation):
    """
    Runs a task (given by identifier) in a remote environment.
    """

    def __init__(
        self,
        initial_state: OperationState,
        *,
        env_name: str,
        workspace_rel_project_root: pathlib.Path,
        task: TaskType,
        dep_versions: Dict[TaskIdentifier, Version],
        output_version: Optional[Version],
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._task = task
        self._dep_versions = dep_versions
        self._project_root = workspace_rel_project_root
        self._output_version = output_version

    @property
    def associated_task(self) -> Optional[TaskType]:
        return self._task

    @property
    def main_task(self) -> Optional[TaskType]:
        return self._task

    @property
    def env_name(self) -> str:
        return self._env_name

    @property
    def output_version(self) -> Optional[Version]:
        return self._output_version

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        # Import this here to avoid import errors for people who have not
        # installed the [envs] extras.
        from conductor.envs.maestro.interface import ExecuteTaskType

        if ctx.envs is None:
            raise MissingEnvSupport()
        if not ctx.git.is_used():
            raise EnvsRequireGit()

        if isinstance(self._task, RunExperiment):
            execute_task_type = ExecuteTaskType.RunExperiment
        elif isinstance(self._task, RunCommand):
            execute_task_type = ExecuteTaskType.RunCommand
        else:
            # Validation should be performed before this point.
            raise InternalError(details=f"Unsupported task type: {type(self._task)}")

        remote_env = ctx.envs.get_remote_env(self._env_name)
        client = remote_env.client()
        workspace_name = remote_env.workspace_name()
        # NOTE: This can be made asynchronous if needed.
        client.execute_task(
            workspace_name,
            self._project_root,
            self._task.identifier,
            self._dep_versions,
            execute_task_type,
            self._output_version,
        )
        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass
