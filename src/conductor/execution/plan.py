import time

from conductor.context import Context
from conductor.errors import ConductorError, TaskNotFound, ConductorAbort
from conductor.execution.task_state import ExecutingTask, TaskState
from conductor.task_identifier import TaskIdentifier
from conductor.utils.time import time_to_readable_string


class ExecutionPlan:
    def __init__(
        self,
        task_identifier: TaskIdentifier,
        run_again: bool = False,
        stop_early: bool = False,
    ):
        # The identifier of the task to run
        self._task_identifier = task_identifier
        # If true, we will always run cached tasks again (even if
        # `TaskType.should_run()` returns `False`)
        self._run_again = run_again
        # If true, we will stop executing a task if one of its dependencies
        # fail.
        self._stop_early = stop_early

    def execute(self, ctx: Context):
        """
        Run the execution plan.
        """
        start = time.time()
        try:
            stack = [ExecutingTask(ctx.task_index.get_task(self._task_identifier))]
            visited = set()
            # Tracks tasks that have finished executing (succeeded,
            # succeeded_cached, skipped, failed). The order of tasks in this
            # list is the order they executed in.
            completed_tasks = []

            # Execute the task dependency graph while respecting dependencies by
            # performing a post-order traversal.
            while len(stack) > 0:
                next_task = stack.pop()
                assert next_task.not_yet_executed()

                # If true, this is the second time we are visiting this task, so
                # this means its dependencies had a chance to execute.
                if next_task.state == TaskState.EXECUTING_DEPS:
                    # Make sure all dependencies succeeded.
                    if not all(map(lambda task: task.succeeded(), next_task.deps)):
                        print("Skipping '{}'.".format(str(next_task.task.identifier)))
                        next_task.set_state(TaskState.SKIPPED)
                        completed_tasks.append(next_task)
                        continue

                    # All dependencies have finished running, can run now.
                    print("Running '{}'...".format(str(next_task.task.identifier)))
                    try:
                        next_task.task.execute(ctx)
                        # If this task succeeded, make sure we commit it to the
                        # version index. This way if later tasks fail, we don't
                        # restart from scratch.
                        ctx.version_index.commit_changes()
                        next_task.set_state(TaskState.SUCCEEDED)
                        completed_tasks.append(next_task)
                    except ConductorError as ex:
                        # The task failed. Abort early if requested by
                        # re-raising the error.
                        ctx.version_index.rollback_changes()
                        next_task.set_state(TaskState.FAILED)
                        next_task.store_error(ex)
                        completed_tasks.append(next_task)
                        if self._stop_early:
                            break

                    # Move on to the next task in the stack.
                    continue

                # This is the first time we're visiting this task in the dependency graph.
                visited.add(next_task.task.identifier)

                # If we do not need to run the task, we do not need to consider
                # its dependencies.
                if not self._run_again and not next_task.task.should_run(ctx):
                    print(
                        "Using cached results for '{}'.".format(
                            str(next_task.task.identifier)
                        )
                    )
                    next_task.set_state(TaskState.SUCCEEDED_CACHED)
                    completed_tasks.append(next_task)
                    continue

                # Process dependencies and then come back to run this task
                next_task.set_state(TaskState.EXECUTING_DEPS)
                stack.append(next_task)

                # Append in reverse order because we pop from the back of the
                # list. This ensures we process dependencies in the order they
                # are listed in the COND file (for the user's convenience).
                for dep in reversed(next_task.task.deps):
                    if dep in visited:
                        continue
                    task_dep = ExecutingTask(ctx.task_index.get_task(dep))
                    next_task.add_dep(task_dep)
                    stack.append(task_dep)

            elapsed = time.time() - start

            # Print the final execution result (succeeded or failed).
            all_succeeded = all(map(lambda task: task.succeeded(), completed_tasks))
            if (
                all_succeeded
                and completed_tasks[-1].task.identifier == self._task_identifier
            ):
                print("✨ Done! (ran for {})".format(time_to_readable_string(elapsed)))

            else:
                # At least one task must have failed.
                first_failed_task = None
                print(
                    "🔴 Task failed. (ran for {})".format(
                        time_to_readable_string(elapsed)
                    )
                )
                print()
                print("Failed task(s):")
                for exe_task in completed_tasks:
                    if exe_task.state != TaskState.FAILED:
                        continue
                    if first_failed_task is None:
                        first_failed_task = exe_task
                    print("  {}".format(exe_task.task.identifier))
                    assert exe_task.stored_error is not None
                    print(
                        "  -> {}".format(
                            exe_task.stored_error.printable_message(ignore_context=True)
                        )
                    )
                print()
                print("Skipped task(s) (because one or more dependencies failed):")
                for exe_task in completed_tasks:
                    if exe_task.state != TaskState.SKIPPED:
                        continue
                    print("  {}".format(exe_task.task.identifier))
                print()

                assert (
                    first_failed_task is not None
                    and first_failed_task.stored_error is not None
                )
                raise first_failed_task.stored_error

        except TaskNotFound:
            # This should not happen. The task graph should be validated before
            # execution.
            ctx.version_index.rollback_changes()
            assert False

        except ConductorAbort:
            ctx.version_index.rollback_changes()
            elapsed = time.time() - start
            print(
                "⚠️  Task aborted. (ran for {})".format(
                    time_to_readable_string(elapsed)
                )
            )
            print()
            raise
