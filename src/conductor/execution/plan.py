from typing import List, Dict, Optional

from conductor.context import Context
from conductor.execution.task import ExecutingTask
from conductor.execution.task_state import TaskState
from conductor.task_identifier import TaskIdentifier


class ExecutionPlan:
    def __init__(
        self,
        task_to_run: ExecutingTask,
        exec_tasks: Dict[TaskIdentifier, ExecutingTask],
        initial_tasks: List[ExecutingTask],
        cached_tasks: List[ExecutingTask],
    ):
        self.task_to_run = task_to_run
        # A subset of the transitive closure of `task_to_run`, containing all
        # tasks that need to be executed (there may be some tasks in the
        # transitive closure that have cached results available).
        self.exec_tasks = exec_tasks
        # Tasks that can be immediately executed (i.e., that have no
        # dependencies).
        self.initial_tasks = initial_tasks
        # Tasks that do not need to be executed because they have relevant
        # cached results available.
        self.cached_tasks = cached_tasks
        # The number of tasks we will need to run.
        self.num_tasks_to_run = sum(
            map(
                lambda _: 1,
                filter(lambda t: t.state == TaskState.QUEUED, self.exec_tasks.values()),
            )
        )

    @classmethod
    def for_task(
        cls,
        task_identifier: TaskIdentifier,
        ctx: Context,
        run_again: bool = False,
        at_least_commit: Optional[str] = None,
    ) -> "ExecutionPlan":
        exec_tasks: Dict[TaskIdentifier, ExecutingTask] = {}
        initial_tasks: List[ExecutingTask] = []
        cached_tasks: List[ExecutingTask] = []

        # Perform a depth-first dependency graph traversal to
        # 1. Prune tasks that do not need to execute (due to having cached results)
        # 2. Link task dependencies
        # 3. Compute the starting tasks (tasks that have no additional dependencies)
        stack = [
            ExecutingTask(
                ctx.task_index.get_task(task_identifier),
                TaskState.PREPROCESS_FIRST,
            )
        ]
        while len(stack) > 0:
            etask = stack.pop()

            if etask.state == TaskState.PREPROCESS_FIRST:
                # First visit to this task.
                exec_tasks[etask.task.identifier] = etask

                # If we do not need to run the task, we do not need to consider
                # its dependencies.
                if not run_again and not etask.task.should_run(ctx, at_least_commit):
                    etask.set_state(TaskState.SUCCEEDED_CACHED)
                    cached_tasks.append(etask)
                    etask.decrement_deps_of_waiting_on()
                    continue

                etask.set_state(TaskState.PREPROCESS_SECOND)
                stack.append(etask)

                # Append in reverse order because we pop from the back of the
                # list. This ensures we process dependencies in the order they
                # are listed in the COND file (for the user's convenience).
                for dep_ident in reversed(etask.task.deps):
                    if dep_ident in exec_tasks:
                        # We do not need to visit this dependency since it was
                        # already visited. But we do want to keep track of its
                        # dependency relationships if the dependency will run.
                        exe_dep = exec_tasks[dep_ident]
                        # Because the dependency graph is acyclic, it cannot be
                        # the case that this dependency is still in a
                        # "preprocessing" state.
                        assert (
                            exe_dep.state == TaskState.QUEUED
                            or exe_dep.state == TaskState.SUCCEEDED_CACHED
                        )
                        if exe_dep.state == TaskState.QUEUED:
                            etask.add_exe_dep(exe_dep)
                            exe_dep.add_dep_of(etask)
                    else:
                        exe_dep = ExecutingTask(
                            ctx.task_index.get_task(dep_ident),
                            TaskState.PREPROCESS_FIRST,
                        )
                        stack.append(exe_dep)
                        etask.add_exe_dep(exe_dep)
                        exe_dep.add_dep_of(etask)

                # All dependencies added.
                etask.reset_waiting_on()

            elif etask.state == TaskState.PREPROCESS_SECOND:
                # Second visit to this node (dependencies have all been
                # processed).
                etask.set_state(TaskState.QUEUED)
                # If this task has no dependencies (or their results are
                # cached), this task can be executed.
                if etask.waiting_on == 0:
                    initial_tasks.append(etask)

            else:
                # Not supposed to happen.
                raise AssertionError

        # Correctness sanity checks.
        # There must be at least one task that can run (since the graph is
        # acyclic), or the result of the task we wanted to run is cached.
        assert task_identifier in exec_tasks
        task_to_run = exec_tasks[task_identifier]
        assert len(initial_tasks) > 0 or task_to_run.state == TaskState.SUCCEEDED_CACHED

        return cls(
            task_to_run=task_to_run,
            exec_tasks=exec_tasks,
            initial_tasks=initial_tasks,
            cached_tasks=cached_tasks,
        )
