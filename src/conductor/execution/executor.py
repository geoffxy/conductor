import errno
import time
import collections
import os
import signal
from typing import Dict, List, Iterable, Tuple

from conductor.context import Context
from conductor.errors import ConductorError, ConductorAbort
from conductor.execution.plan import ExecutionPlan
from conductor.execution.task import ExecutingTask
from conductor.execution.task_state import TaskState
from conductor.task_types.base import TaskExecutionHandle
from conductor.utils.colored_output import (
    print_bold,
    print_cyan,
    print_green,
    print_red,
    print_yellow,
)
from conductor.utils.sigchld import SigchldHelper
from conductor.utils.time import time_to_readable_string


class _ReadyToRunQueue:
    def __init__(self):
        self._sequential_tasks = collections.deque()
        self._parallel_tasks = collections.deque()

    def load(self, initial_tasks: Iterable[ExecutingTask]):
        for task in initial_tasks:
            self.enqueue_task(task)

    def has_tasks(self) -> bool:
        return (len(self._sequential_tasks) > 0) or (len(self._parallel_tasks) > 0)

    def has_parallelizable_tasks(self) -> bool:
        return len(self._parallel_tasks) > 0

    def enqueue_task(self, task: ExecutingTask) -> None:
        if task.task.parallelizable:
            self._parallel_tasks.append(task)
        else:
            self._sequential_tasks.append(task)

    def dequeue_next(self) -> ExecutingTask:
        if self.has_parallelizable_tasks():
            return self._parallel_tasks.popleft()
        else:
            return self._sequential_tasks.popleft()

    def clear(self) -> None:
        self._sequential_tasks.clear()
        self._parallel_tasks.clear()


class _InflightTasks:
    def __init__(self):
        self._processes: Dict[int, Tuple[TaskExecutionHandle, ExecutingTask]] = {}
        self._sync_tasks: List[Tuple[TaskExecutionHandle, ExecutingTask]] = []

    def add_task(self, handle: TaskExecutionHandle, task: ExecutingTask) -> None:
        if handle.is_sync:
            self._sync_tasks.append((handle, task))
        else:
            assert handle.pid is not None
            self._processes[handle.pid] = (handle, task)

    def __len__(self) -> int:
        return len(self._processes) + len(self._sync_tasks)

    def has_sync_tasks(self) -> bool:
        return len(self._sync_tasks) > 0

    def wait_for_next_task(self) -> Tuple[TaskExecutionHandle, ExecutingTask]:
        if len(self._sync_tasks) > 0:
            return self._sync_tasks.pop()

        # Wait for the next child process to finish.
        while True:
            pid, returncode = SigchldHelper.instance().wait()
            if pid in self._processes:
                break
        assert pid in self._processes
        handle, task = self._processes[pid]
        del self._processes[pid]
        handle.returncode = returncode
        return handle, task

    def terminate_processes(self) -> None:
        # Send SIGTERM to each process' process group (i.e., the subprocess and
        # its child processes).
        for handle, _ in self._processes.values():
            try:
                if handle.pid is None:
                    continue
                group_id = os.getpgid(handle.pid)
                if group_id < 0:
                    continue
                os.killpg(group_id, signal.SIGTERM)
            except OSError as ex:
                # Ignore errors due to the process not existing or having no
                # children.
                if ex.errno != errno.ESRCH and ex.errno != errno.ECHILD:
                    raise

    def clear(self) -> None:
        self.terminate_processes()
        self._processes.clear()
        self._sync_tasks.clear()


class Executor:
    def __init__(self, execution_slots: int):
        assert execution_slots > 0
        self._slots = execution_slots
        self._available_slots = list(reversed(range(self._slots)))

        self._ready_to_run = _ReadyToRunQueue()
        self._inflight_tasks = _InflightTasks()
        self._completed_tasks: List[ExecutingTask] = []
        self._running_parallel = False
        self._num_tasks_to_run = 0
        self._num_tasks_dequeued = 0

    def run_plan(
        self, plan: ExecutionPlan, ctx: Context, stop_on_first_error: bool = False
    ):
        try:
            self._reset()
            self._num_tasks_to_run = plan.num_tasks_to_run
            start = time.time()

            # 1. Print out any cached tasks.
            for cached_task in plan.cached_tasks:
                print_cyan(
                    "✓ Using cached results for {}.".format(
                        str(cached_task.task.identifier)
                    )
                )

            # 2. Run the tasks as they become eligible for execution.
            should_stop = False
            self._ready_to_run.load(plan.initial_tasks)
            with SigchldHelper.instance().track():
                while self._ready_to_run.has_tasks() or len(self._inflight_tasks) > 0:
                    should_stop = self._launch_tasks_if_able(ctx, stop_on_first_error)
                    if should_stop:
                        break

                    if len(self._inflight_tasks) == 0:
                        # There may be no in-flight tasks if the last ready-to-run
                        # task failed or was skipped.
                        continue

                    should_stop = self._wait_for_next_inflight_task(
                        ctx, stop_on_first_error
                    )
                    if should_stop:
                        break

            # Only has an effect if we exited the loop above early due to
            # encountering an error.
            self._inflight_tasks.terminate_processes()

            # 3. Report the results.
            self._report_execution_results(plan, elapsed_time=(time.time() - start))

        except ConductorAbort:
            self._inflight_tasks.terminate_processes()
            elapsed = time.time() - start
            print()
            print_yellow(
                "🔸 Task aborted. {}".format(self._get_elapsed_time_string(elapsed)),
                bold=True,
            )
            print()
            raise

    def _reset(self) -> None:
        self._ready_to_run.clear()
        self._completed_tasks.clear()
        self._inflight_tasks.clear()
        self._running_parallel = False
        self._available_slots = list(reversed(range(self._slots)))
        self._num_tasks_to_run = 0
        self._num_tasks_dequeued = 0

    def _launch_tasks_if_able(self, ctx: Context, stop_on_first_error: bool) -> bool:
        """
        Launches as many tasks as possible while respecting the task's
        parallelization setting and the number of execution slots available.

        Returns `True` if an error occurs and `stop_on_first_error` is set to `True.
        """
        while True:
            can_launch_any_ready_task = (
                self._ready_to_run.has_tasks() and len(self._inflight_tasks) == 0
            )
            can_launch_parallelizable_task = (
                self._running_parallel
                and len(self._inflight_tasks) < self._slots
                and self._ready_to_run.has_parallelizable_tasks()
            )

            if not can_launch_any_ready_task and not can_launch_parallelizable_task:
                break

            # Parallelizable tasks are prioritized (dequeued first).
            next_task = self._ready_to_run.dequeue_next()
            prev_running_parallel = self._running_parallel
            self._running_parallel = next_task.task.parallelizable
            self._num_tasks_dequeued += 1

            # For output cosmetics. We add empty lines between task outputs to
            # help distinguish their outputs. But this extra empty line is not
            # useful when more than one task is running in parallel. So once
            # Conductor switches to running tasks in parallel, we want to stop
            # printing the extra newline character.
            avoid_leading_newline = (
                prev_running_parallel and self._running_parallel and self._slots > 1
            )

            if not next_task.exe_deps_succeeded():
                # At least one dependency failed, so we need to skip this task.
                if not avoid_leading_newline:
                    print()
                print_yellow(
                    "✱ Skipping {}. {}".format(
                        str(next_task.task.identifier), self._get_progress_string()
                    )
                )
                next_task.set_state(TaskState.SKIPPED)
                self._process_finished_task(next_task)
            else:
                if not avoid_leading_newline:
                    print()
                print_cyan(
                    "✱ Running {}... {}".format(
                        str(next_task.task.identifier), self._get_progress_string()
                    )
                )
                try:
                    slot = (
                        self._available_slots[-1]
                        if self._running_parallel and self._slots > 1
                        else None
                    )
                    handle = next_task.task.start_execution(ctx, slot)
                    handle.slot = slot
                    self._inflight_tasks.add_task(handle, next_task)
                    if slot is not None:
                        self._available_slots.pop()
                except ConductorAbort:
                    next_task.set_state(TaskState.ABORTED)
                    # N.B. A slot may be leaked here, but it does not matter
                    # because we are aborting the execution.
                    raise
                except ConductorError as ex:
                    next_task.store_error(ex)
                    next_task.set_state(TaskState.FAILED)
                    self._process_finished_task(next_task)
                    self._print_task_failed(next_task)
                    if stop_on_first_error:
                        return True

        return False

    def _wait_for_next_inflight_task(
        self, ctx: Context, stop_on_first_error: bool
    ) -> bool:
        """
        Waits for the next inflight task to complete (and processes it).

        Returns `True` if an error occurs and `stop_on_first_error` is set to `True.
        """
        assert len(self._inflight_tasks) > 0

        error_occurred = False
        handle, task = self._inflight_tasks.wait_for_next_task()
        try:
            task.task.finish_execution(handle, ctx)
            task.set_state(TaskState.SUCCEEDED)
            print_green("✓ {} completed successfully.".format(task.task.identifier))
        except ConductorAbort:
            task.set_state(TaskState.ABORTED)
            # N.B. A slot may be leaked here, but it does not matter because we
            # are aborting the execution.
            raise
        except ConductorError as ex:
            task.store_error(ex)
            task.set_state(TaskState.FAILED)
            error_occurred = True
            self._print_task_failed(task)

        if handle.slot is not None:
            self._available_slots.append(handle.slot)
        self._process_finished_task(task)

        return error_occurred and stop_on_first_error

    def _process_finished_task(self, finished_task: ExecutingTask) -> None:
        self._completed_tasks.append(finished_task)
        finished_task.decrement_deps_of_waiting_on()
        for dep_of in finished_task.deps_of:
            if dep_of.waiting_on > 0:
                continue
            self._ready_to_run.enqueue_task(dep_of)

    def _report_execution_results(self, plan: ExecutionPlan, elapsed_time: float):
        all_succeeded = all(map(lambda task: task.succeeded(), self._completed_tasks))
        # We executed at least one task.
        # The main task we wanted to run should always be the last
        # completed task (its dependencies must be executed first).
        main_task_executed = (
            len(self._completed_tasks) > 0
            and self._completed_tasks[-1].task.identifier
            == plan.task_to_run.task.identifier
        )
        # We did not run any tasks, so the task we wanted to run
        # must have been cached.
        main_task_cached = (
            len(self._completed_tasks) == 0
            and plan.task_to_run.state == TaskState.SUCCEEDED_CACHED
        )

        # Print the final execution result (succeeded or failed).
        if all_succeeded and (main_task_executed or main_task_cached):
            print()
            print_bold("✨ Done! {}".format(self._get_elapsed_time_string(elapsed_time)))

        else:
            # At least one task must have failed.
            failed_tasks: List[ExecutingTask] = []
            skipped_tasks: List[ExecutingTask] = []
            for exe_task in self._completed_tasks:
                if exe_task.state == TaskState.SKIPPED:
                    skipped_tasks.append(exe_task)
                elif exe_task.state == TaskState.FAILED:
                    failed_tasks.append(exe_task)
            assert len(failed_tasks) > 0
            print()
            print_red(
                "🔴 Task failed. {}".format(self._get_elapsed_time_string(elapsed_time)),
                bold=True,
            )
            print()
            print_bold("Failed task(s):")
            for failed in failed_tasks:
                print("  {}".format(failed.task.identifier))
                assert failed.stored_error is not None
                print(
                    "    {}".format(
                        failed.stored_error.printable_message(omit_file_context=True)
                    )
                )
            print()
            if len(skipped_tasks) > 0:
                print_bold("Skipped task(s) (one or more dependencies failed):")
                for skipped in skipped_tasks:
                    print("  {}".format(skipped.task.identifier))
                print()

            assert failed_tasks[0].stored_error is not None
            raise failed_tasks[0].stored_error

    def _print_task_failed(self, task: ExecutingTask):
        print_red("✘ {} failed.".format(task.task.identifier))

    def _get_progress_string(self):
        return "({}/{})".format(str(self._num_tasks_dequeued), self._num_tasks_to_run)

    def _get_elapsed_time_string(self, elapsed: float):
        return "(Ran for {}.)".format(time_to_readable_string(elapsed))
