from typing import Dict, List, Optional

from conductor.context import Context
from conductor.execution.ops.combine_outputs import CombineOutputs
from conductor.execution.ops.operation import Operation
from conductor.execution.ops.run_task_executable import RunTaskExecutable
from conductor.execution.planning.lowering import LoweringTask, LoweringState
from conductor.execution.plan2 import ExecutionPlan2
from conductor.execution.task_state import TaskState
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType
from conductor.task_types.group import Group
from conductor.task_types.combine import Combine
from conductor.task_types.run import RunCommand, RunExperiment


class ExecutionPlanner:
    def __init__(self, ctx: Context) -> None:
        self._ctx = ctx

    def create_plan_for(
        self,
        task_id: TaskIdentifier,
        run_again: bool = False,
        at_least_commit: Optional[str] = None,
    ) -> "ExecutionPlan2":
        """
        Creates an `ExecutionPlan2` for the given task.

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
                if isinstance(lt.task, Group):
                    # No operation needed because there is nothing to run; we
                    # just need to propagate the dependencies forward.
                    for dep in lt.deps:
                        lt.output_ops.extend(dep.output_ops)
                    num_tasks_to_run += 1

                else:
                    # These task types always produce at least one `Operation`.
                    if isinstance(lt.task, RunExperiment):
                        exp_version = lt.task.create_new_version(self._ctx)
                        output_path = lt.task.get_output_path(self._ctx)
                        assert output_path is not None
                        new_op: Operation = RunTaskExecutable(
                            initial_state=TaskState.QUEUED,
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
                            initial_state=TaskState.QUEUED,
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
                        new_op = CombineOutputs(
                            initial_state=TaskState.QUEUED,
                            task=lt.task,
                            identifier=lt.task.identifier,
                            output_path=output_path,
                            deps_output_paths=lt.task.get_deps_output_paths(self._ctx),
                        )

                    else:
                        # This indicates a bug: we added a new task type but did
                        # not update the planner.
                        raise NotImplementedError(f"Unsupported task type: {lt.task}")

                    # Hook the new dependency into the graph.
                    for dep in lt.deps:
                        for dep_op in dep.output_ops:
                            new_op.add_exe_dep(dep_op)
                            dep_op.add_dep_of(new_op)
                    lt.output_ops.append(new_op)

                    # If this operation has no dependencies, it is part of
                    # `initial_operations`.
                    if len(lt.deps) == 0:
                        initial_operations.append(new_op)

                    all_ops.append(new_op)

                    # N.B. Right now there's a 1-to-1 correspondence between
                    # tasks and operations. But with remote execution, this will
                    # change.
                    num_tasks_to_run += 1

        return ExecutionPlan2(
            task_to_run=task_to_run,
            all_ops=all_ops,
            initial_ops=initial_operations,
            cached_tasks=cached_tasks,
            num_tasks_to_run=num_tasks_to_run,
        )
