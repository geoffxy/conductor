from typing import Dict, List, Optional

from conductor.context import Context
from conductor.errors import InternalError, EnvsRequireGit
from conductor.execution.ops.combine_outputs import CombineOutputs
from conductor.execution.ops.noop import NoOp
from conductor.execution.ops.operation import Operation
from conductor.execution.ops.run_remote_task import RunRemoteTask
from conductor.execution.ops.run_task_executable import RunTaskExecutable
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.transfer_repo import TransferRepo
from conductor.execution.ops.transfer_results import TransferResults, TransferDirection
from conductor.execution.planning.lowering import LoweringTask, LoweringState
from conductor.execution.plan import ExecutionPlan
from conductor.execution.operation_state import OperationState
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType
from conductor.task_types.combine import Combine
from conductor.task_types.environment import Environment
from conductor.task_types.group import Group
from conductor.task_types.run import RunCommand, RunExperiment


class ExecutionPlanner:
    def __init__(self, ctx: Context) -> None:
        self._ctx = ctx

    def create_plan_for(
        self,
        task_id: TaskIdentifier,
        run_again: bool = False,
        at_least_commit: Optional[str] = None,
    ) -> "ExecutionPlan":
        """
        Creates an `ExecutionPlan` for the given task.

        This function converts the task graph into a physical operation graph,
        eliminating tasks that do not need to execute (due to having cached
        results).
        """

        all_ops: List[Operation] = []
        initial_operations: List[Operation] = []
        cached_tasks: List[TaskType] = []
        task_to_run = self._ctx.task_index.get_task(task_id)
        num_tasks_to_run = 0

        # First pass (depth first):
        # 1. Prune tasks that do not need to execute (due to having cached results).
        # 2. Link task dependencies.
        root = LoweringTask.initial(task_to_run)
        stack = [root]
        visited: Dict[TaskIdentifier, LoweringTask] = {}
        while len(stack) > 0:
            lt = stack.pop()

            if lt.state == LoweringState.FIRST_VISIT:
                # First visit to this task.
                visited[lt.task.identifier] = lt

                if not run_again and not lt.task.should_run(self._ctx, at_least_commit):
                    # This task does not need to be executed again, so we do not
                    # traverse further.
                    cached_tasks.append(lt.task)
                    continue

                lt.state = LoweringState.SECOND_VISIT
                stack.append(lt)

                # Append in reverse order because we pop from the back of the
                # list. This ensures we process dependencies in the order they
                # are listed in the COND file (for the user's convenience).
                for dep_ident in reversed(lt.task.deps):
                    if dep_ident in visited:
                        # Add the dependency relationship, but do not traverse
                        # its dependencies because we already visited.
                        dep = visited[dep_ident]
                        lt.deps.append(dep)
                        continue

                    dep = LoweringTask.initial(self._ctx.task_index.get_task(dep_ident))
                    lt.deps.append(dep)
                    stack.append(dep)

            elif lt.state == LoweringState.SECOND_VISIT:
                if lt.task.runs_in_env:
                    ops = self._create_env_operations(lt)
                    assert len(ops) > 1

                    # ops[0] is the first task to run, ops[-1] is the last.
                    # So the deps of the `lt` task should be the deps of
                    # `ops[0]`.
                    for dep in lt.deps:
                        for dep_op in dep.output_ops:
                            ops[0].add_exe_dep(dep_op)
                            dep_op.add_dep_of(ops[0])
                    lt.output_ops.append(ops[-1])

                    if len(ops[0].exe_deps) == 0:
                        initial_operations.append(ops[0])

                    all_ops.extend(ops)
                    num_tasks_to_run += len(ops)

                else:
                    new_op = self._create_local_operation(lt)

                    # Hook the new dependency into the graph.
                    for dep in lt.deps:
                        for dep_op in dep.output_ops:
                            new_op.add_exe_dep(dep_op)
                            dep_op.add_dep_of(new_op)
                    lt.output_ops.append(new_op)

                    # If this operation has no dependencies, it is part of
                    # `initial_operations`.
                    if len(new_op.exe_deps) == 0:
                        initial_operations.append(new_op)

                    all_ops.append(new_op)
                    num_tasks_to_run += 1

        return ExecutionPlan(
            task_to_run=task_to_run,
            all_ops=all_ops,
            initial_ops=initial_operations,
            cached_tasks=cached_tasks,
            num_tasks_to_run=num_tasks_to_run,
        )

    def _create_local_operation(self, lt: LoweringTask) -> Operation:
        """
        This is used when the task maps to a single operation (when the task
        runs locally).
        """

        if isinstance(lt.task, RunExperiment):
            exp_version = lt.task.create_new_version(self._ctx)
            output_path = lt.task.get_output_path(self._ctx)
            assert output_path is not None
            new_op: Operation = RunTaskExecutable(
                initial_state=OperationState.QUEUED,
                identifier=lt.task.identifier,
                task=lt.task,
                run=lt.task.raw_run,
                args=lt.task.args,
                options=lt.task.options,
                working_path=lt.task.get_working_path(self._ctx),
                output_path=output_path,
                deps_output_paths=lt.task.get_deps_output_paths(self._ctx),
                record_output=True,
                version_to_record=exp_version,
                serialize_args_options=True,
                parallelizable=lt.task.parallelizable,
            )

        elif isinstance(lt.task, RunCommand):
            output_path = lt.task.get_output_path(self._ctx)
            assert output_path is not None
            new_op = RunTaskExecutable(
                initial_state=OperationState.QUEUED,
                task=lt.task,
                identifier=lt.task.identifier,
                run=lt.task.raw_run,
                args=lt.task.args,
                options=lt.task.options,
                working_path=lt.task.get_working_path(self._ctx),
                output_path=output_path,
                deps_output_paths=lt.task.get_deps_output_paths(self._ctx),
                record_output=False,
                version_to_record=None,
                serialize_args_options=False,
                parallelizable=lt.task.parallelizable,
            )

        elif isinstance(lt.task, Combine):
            output_path = lt.task.get_output_path(self._ctx)
            assert output_path is not None
            # Pairs of `(dependency task id, output path)`.
            dep_output_paths = []
            for task_dep_id in lt.task.deps:
                task = self._ctx.task_index.get_task(task_dep_id)
                task_output_path = task.get_output_path(self._ctx)
                if task_output_path is not None:
                    dep_output_paths.append((task_dep_id, task_output_path))
            new_op = CombineOutputs(
                initial_state=OperationState.QUEUED,
                task=lt.task,
                identifier=lt.task.identifier,
                output_path=output_path,
                deps_output_paths=dep_output_paths,
            )

        elif isinstance(lt.task, Group):
            # No operation needed because there is nothing to run; we
            # just need to propagate the dependencies forward.
            new_op = NoOp(
                initial_state=OperationState.QUEUED,
                identifier=lt.task.identifier,
                task=lt.task,
            )

        else:
            # This indicates a bug: we added a new task type but did
            # not update the planner.
            raise InternalError(details=f"Unsupported task type: {lt.task}")

        return new_op

    def _create_env_operations(self, lt: LoweringTask) -> List[Operation]:
        """
        This is used when the task maps to multiple operations (when the task
        runs inside a remote environment).
        """
        assert isinstance(lt.task, RunCommand) or isinstance(lt.task, RunExperiment)
        assert lt.task.env is not None

        git_root = self._ctx.git.git_root()
        if git_root is None:
            raise EnvsRequireGit()

        # Each remote task maps to the following operations:
        # - Start the remote env
        # - Transfer repo
        # - Transfer dependency outputs
        # - Run task
        # - Transfer results back
        # - Shutdown the remote env

        env_task = self._ctx.task_index.get_task(lt.task.env)
        assert isinstance(env_task, Environment)
        env_name = env_task.identifier.name
        env_startstop_working_path = env_task.get_working_path(self._ctx)
        workspace_rel_project_root = self._ctx.project_root.relative_to(git_root)

        if isinstance(lt.task, RunExperiment):
            output_version = lt.task.create_new_version(self._ctx)
        else:
            output_version = None

        # Collect dependencies.
        versioned_task_deps = []
        unversioned_task_deps = []
        for dep in lt.task.deps:
            dep_task = self._ctx.task_index.get_task(dep)
            out_version = dep_task.get_output_version(self._ctx)
            if out_version is not None:
                versioned_task_deps.append((dep, out_version))
            else:
                unversioned_task_deps.append(dep)

        ops: List[Operation] = []
        start_env = StartRemoteEnv(
            initial_state=OperationState.QUEUED,
            env_name=env_name,
            start_runnable=env_task.start,
            working_path=env_startstop_working_path,
            remote_host=env_task.host,
            remote_user=env_task.user,
        )
        ops.append(start_env)

        transfer_repo = TransferRepo(
            initial_state=OperationState.QUEUED,
            env_name=env_name,
        )
        ops.append(transfer_repo)

        if len(versioned_task_deps) > 0 or len(unversioned_task_deps) > 0:
            transfer_to_env = TransferResults(
                initial_state=OperationState.QUEUED,
                env_name=env_name,
                direction=TransferDirection.ToEnv,
                workspace_rel_project_root=workspace_rel_project_root,
                versioned_tasks=versioned_task_deps,
                unversioned_tasks=unversioned_task_deps,
            )
            ops.append(transfer_to_env)

        run_task = RunRemoteTask(
            initial_state=OperationState.QUEUED,
            env_name=env_name,
            workspace_rel_project_root=workspace_rel_project_root,
            task=lt.task,
            dep_versions={k: v for k, v in versioned_task_deps},
            output_version=output_version,
        )
        ops.append(run_task)

        transfer_from_env = TransferResults(
            initial_state=OperationState.QUEUED,
            env_name=env_name,
            direction=TransferDirection.FromEnv,
            workspace_rel_project_root=workspace_rel_project_root,
            versioned_tasks=(
                [] if output_version is None else [(lt.task.identifier, output_version)]
            ),
            unversioned_tasks=(
                [] if output_version is not None else [lt.task.identifier]
            ),
        )
        ops.append(transfer_from_env)

        shutdown_env = ShutdownRemoteEnv(
            initial_state=OperationState.QUEUED,
            env_name=env_name,
            shutdown_runnable=env_task.stop,
            working_path=env_startstop_working_path,
        )
        ops.append(shutdown_env)

        _link_ops(ops)
        return ops


def _link_ops(ops: List[Operation]) -> None:
    """
    Links operations together based on dependencies.
    """
    for idx, op in enumerate(ops):
        if idx == 0:
            continue
        prev_op = ops[idx - 1]
        prev_op.add_dep_of(op)
        op.add_exe_dep(prev_op)
