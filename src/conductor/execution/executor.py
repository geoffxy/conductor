import time
import collections
from typing import List

from conductor.context import Context
from conductor.errors import ConductorError, TaskNotFound, ConductorAbort
from conductor.execution.plan import ExecutionPlan
from conductor.execution.task import ExecutingTask
from conductor.execution.task_state import TaskState
from conductor.utils.time import time_to_readable_string


class Executor:
    def run_plan(self, plan: ExecutionPlan, ctx: Context, stop_early: bool = False):
        start = time.time()
        try:
            # 1. Print out any cached tasks.
            for cached_task in plan.cached_tasks:
                print(
                    "Using cached results for {}.".format(
                        str(cached_task.task.identifier)
                    )
                )

            # A queue of tasks that are ready for execution (their dependencies
            # have completed).
            ready_to_run = collections.deque(plan.initial_tasks)

            # Tracks tasks that have finished executing (succeeded,
            # succeeded_cached, skipped, failed). The order of tasks in this
            # list is the order they executed in.
            completed_tasks: List[ExecutingTask] = []

            while len(ready_to_run) > 0:
                next_task = ready_to_run.popleft()

                # Make sure all dependencies succeeded. Otherwise we need to
                # skip this task.
                if not next_task.exe_deps_succeeded():
                    print("Skipping {}.".format(str(next_task.task.identifier)))
                    next_task.set_state(TaskState.SKIPPED)
                else:
                    # All dependencies have successfully run; can run now.
                    print("Running {}...".format(str(next_task.task.identifier)))
                    try:
                        handle = next_task.task.start_execution(ctx)
                        if not handle.already_completed:
                            handle.get_process().wait()
                        next_task.task.finish_execution(handle, ctx)
                        next_task.set_state(TaskState.SUCCEEDED)
                    except ConductorAbort:
                        # User-initiated aborts are not treated as a task failure.
                        ctx.version_index.rollback_changes()
                        next_task.set_state(TaskState.ABORTED)
                        raise
                    except ConductorError as ex:
                        # The task failed. Abort early if requested by
                        # re-raising the error.
                        ctx.version_index.rollback_changes()
                        next_task.set_state(TaskState.FAILED)
                        next_task.store_error(ex)
                        if stop_early:
                            # To allow the failure to be printed below.
                            completed_tasks.append(next_task)
                            break

                completed_tasks.append(next_task)
                # Enqueue any tasks that now become ready to run because this
                # task executed.
                next_task.decrement_deps_of_waiting_on()
                for dep_of in next_task.deps_of:
                    if dep_of.waiting_on > 0:
                        continue
                    ready_to_run.append(dep_of)

            elapsed = time.time() - start

            all_succeeded = all(map(lambda task: task.succeeded(), completed_tasks))
            # We executed at least one task.
            # The main task we wanted to run should always be the last
            # completed task (its dependencies must be executed first).
            main_task_executed = (
                len(completed_tasks) > 0
                and completed_tasks[-1].task.identifier
                == plan.task_to_run.task.identifier
            )
            # We did not run any tasks, so the task we wanted to run
            # must have been cached.
            main_task_cached = (
                len(completed_tasks) == 0
                and plan.task_to_run.state == TaskState.SUCCEEDED_CACHED
            )

            # Print the final execution result (succeeded or failed).
            if all_succeeded and (main_task_executed or main_task_cached):
                print("✨ Done! (ran for {})".format(time_to_readable_string(elapsed)))

            else:
                # At least one task must have failed.
                failed_tasks: List[ExecutingTask] = []
                skipped_tasks: List[ExecutingTask] = []
                for exe_task in completed_tasks:
                    if exe_task.state == TaskState.SKIPPED:
                        skipped_tasks.append(exe_task)
                    elif exe_task.state == TaskState.FAILED:
                        failed_tasks.append(exe_task)
                assert len(failed_tasks) > 0
                print(
                    "🔴 Task failed. (ran for {})".format(
                        time_to_readable_string(elapsed)
                    )
                )
                print()
                print("Failed task(s):")
                for failed in failed_tasks:
                    print("  {}".format(failed.task.identifier))
                    assert failed.stored_error is not None
                    print(
                        "    {}".format(
                            failed.stored_error.printable_message(
                                omit_file_context=True
                            )
                        )
                    )
                print()
                if len(skipped_tasks) > 0:
                    print("Skipped task(s) (one or more dependencies failed):")
                    for skipped in skipped_tasks:
                        print("  {}".format(skipped.task.identifier))
                    print()

                assert failed_tasks[0].stored_error is not None
                raise failed_tasks[0].stored_error

        except TaskNotFound as ex:
            # This should not happen. The task graph should be validated before
            # execution.
            ctx.version_index.rollback_changes()
            raise AssertionError from ex

        except ConductorAbort:
            ctx.version_index.rollback_changes()
            elapsed = time.time() - start
            print(
                "🔸 Task aborted. (ran for {})".format(time_to_readable_string(elapsed))
            )
            print()
            raise
