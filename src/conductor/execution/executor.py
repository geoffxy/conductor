import errno
import time
import collections
import os
import signal
from typing import Dict, List, Iterable, Tuple, Deque

from conductor.context import Context
from conductor.errors import ConductorError, ConductorAbort
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.ops.operation import Operation
from conductor.execution.plan import ExecutionPlan
from conductor.execution.operation_state import OperationState
from conductor.task_identifier import TaskIdentifier
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
    def __init__(self) -> None:
        self._sequential_ops: Deque[Operation] = collections.deque()
        self._parallel_ops: Deque[Operation] = collections.deque()

    def load(self, initial_ops: Iterable[Operation]) -> None:
        for op in initial_ops:
            self.enqueue_op(op)

    def has_ops(self) -> bool:
        return (len(self._sequential_ops) > 0) or (len(self._parallel_ops) > 0)

    def has_parallelizable_ops(self) -> bool:
        return len(self._parallel_ops) > 0

    def enqueue_op(self, op: Operation) -> None:
        if op.parallelizable:
            self._parallel_ops.append(op)
        else:
            self._sequential_ops.append(op)

    def dequeue_next(self) -> Operation:
        if self.has_parallelizable_ops():
            return self._parallel_ops.popleft()
        else:
            return self._sequential_ops.popleft()

    def clear(self) -> None:
        self._sequential_ops.clear()
        self._parallel_ops.clear()


class _InflightOperations:
    def __init__(self) -> None:
        self._processes: Dict[int, Tuple[OperationExecutionHandle, Operation]] = {}
        self._sync_ops: List[Tuple[OperationExecutionHandle, Operation]] = []

    def add_op(self, handle: OperationExecutionHandle, op: Operation) -> None:
        if handle.is_sync:
            self._sync_ops.append((handle, op))
        else:
            assert handle.pid is not None
            self._processes[handle.pid] = (handle, op)

    def __len__(self) -> int:
        return len(self._processes) + len(self._sync_ops)

    def has_sync_ops(self) -> bool:
        return len(self._sync_ops) > 0

    def wait_for_next_op(self) -> Tuple[OperationExecutionHandle, Operation]:
        if len(self._sync_ops) > 0:
            return self._sync_ops.pop()

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
        self._sync_ops.clear()


class Executor:
    def __init__(self, execution_slots: int, silent: bool = False) -> None:
        assert execution_slots > 0
        self._slots = execution_slots
        self._available_slots = list(reversed(range(self._slots)))

        self._ready_to_run = _ReadyToRunQueue()
        self._inflight_ops = _InflightOperations()
        self._completed_ops: List[Operation] = []
        self._running_parallel = False
        self._num_tasks_to_run = 0
        self._num_tasks_dequeued = 0

        # If `silent` is set to `True`, the executor will not print any output
        self._silent = silent

    def run_plan(
        self,
        plan: ExecutionPlan,
        ctx: Context,
        stop_on_first_error: bool = False,
    ):
        try:
            self._reset()
            plan.reset_waiting_on()
            self._num_tasks_to_run = plan.num_tasks_to_run
            start = time.time()

            # 1. Print out any cached tasks.
            if not self._silent:
                for cached_task in plan.cached_tasks:
                    print_cyan(
                        "✓ Using cached results for {}.".format(
                            str(cached_task.identifier)
                        )
                    )

            # 2. Run the operations as they become eligible for execution.
            should_stop = False
            self._ready_to_run.load(plan.initial_ops)
            with SigchldHelper.instance().track():
                while self._ready_to_run.has_ops() or len(self._inflight_ops) > 0:
                    should_stop = self._launch_ops_if_able(ctx, stop_on_first_error)
                    if should_stop:
                        break

                    if len(self._inflight_ops) == 0:
                        # There may be no in-flight ops if the last ready-to-run
                        # op failed or was skipped.
                        continue

                    should_stop = self._wait_for_next_inflight_op(
                        ctx, stop_on_first_error
                    )
                    if should_stop:
                        break

            # Only has an effect if we exited the loop above early due to
            # encountering an error.
            self._inflight_ops.terminate_processes()

            # 3. Report the results.
            self._report_execution_results(plan, elapsed_time=(time.time() - start))

        except ConductorAbort:
            self._inflight_ops.terminate_processes()
            elapsed = time.time() - start
            if not self._silent:
                print()
                print_yellow(
                    "🔸 Task aborted. {}".format(
                        self._get_elapsed_time_string(elapsed)
                    ),
                    bold=True,
                )
                print()
            raise

    def _reset(self) -> None:
        self._ready_to_run.clear()
        self._completed_ops.clear()
        self._inflight_ops.clear()
        self._running_parallel = False
        self._available_slots = list(reversed(range(self._slots)))
        self._num_tasks_to_run = 0
        self._num_tasks_dequeued = 0

    def _launch_ops_if_able(self, ctx: Context, stop_on_first_error: bool) -> bool:
        """
        Launches as many operations as possible while respecting the operation's
        parallelization setting and the number of execution slots available.

        Returns `True` if an error occurs and `stop_on_first_error` is set to `True.
        """
        while True:
            can_launch_any_ready_op = (
                self._ready_to_run.has_ops() and len(self._inflight_ops) == 0
            )
            can_launch_parallelizable_op = (
                self._running_parallel
                and len(self._inflight_ops) < self._slots
                and self._ready_to_run.has_parallelizable_ops()
            )

            if not can_launch_any_ready_op and not can_launch_parallelizable_op:
                break

            # Parallelizable tasks are prioritized (dequeued first).
            next_op = self._ready_to_run.dequeue_next()
            prev_running_parallel = self._running_parallel
            self._running_parallel = next_op.parallelizable
            if next_op.main_task is not None:
                self._num_tasks_dequeued += 1

            # For output cosmetics. We add empty lines between task outputs to
            # help distinguish their outputs. But this extra empty line is not
            # useful when more than one task is running in parallel. So once
            # Conductor switches to running tasks in parallel, we want to stop
            # printing the extra newline character.
            avoid_leading_newline = (
                prev_running_parallel and self._running_parallel and self._slots > 1
            )

            if not next_op.exe_deps_succeeded():
                # At least one dependency failed, so we need to skip this task.
                if next_op.main_task is not None and not self._silent:
                    # Print information about the task that is being skipped.
                    if not avoid_leading_newline:
                        print()
                    print_yellow(
                        "✱ Skipping {}. {}".format(
                            str(next_op.main_task.identifier),
                            self._get_progress_string(),
                        )
                    )
                next_op.set_state(OperationState.SKIPPED)
                self._process_finished_op(next_op)
            else:
                if next_op.main_task is not None and not self._silent:
                    if not avoid_leading_newline:
                        print()
                    print_cyan(
                        "✱ Running {}... {}".format(
                            str(next_op.main_task.identifier),
                            self._get_progress_string(),
                        )
                    )
                try:
                    slot = (
                        self._available_slots[-1]
                        if self._running_parallel and self._slots > 1
                        else None
                    )
                    handle = next_op.start_execution(ctx, slot)
                    handle.slot = slot
                    self._inflight_ops.add_op(handle, next_op)
                    if slot is not None:
                        self._available_slots.pop()
                except ConductorAbort:
                    next_op.set_state(OperationState.ABORTED)
                    # N.B. A slot may be leaked here, but it does not matter
                    # because we are aborting the execution.
                    raise
                except ConductorError as ex:
                    next_op.store_error(ex)
                    next_op.set_state(OperationState.FAILED)
                    self._process_finished_op(next_op)
                    self._print_op_failed(next_op)
                    if stop_on_first_error:
                        return True

        return False

    def _wait_for_next_inflight_op(
        self, ctx: Context, stop_on_first_error: bool
    ) -> bool:
        """
        Waits for the next inflight operation to complete (and processes it).

        Returns `True` if an error occurs and `stop_on_first_error` is set to `True.
        """
        assert len(self._inflight_ops) > 0

        error_occurred = False
        handle, op = self._inflight_ops.wait_for_next_op()
        try:
            op.finish_execution(handle, ctx)
            op.set_state(OperationState.SUCCEEDED)
            if op.main_task is not None and not self._silent:
                print_green(
                    "✓ {} completed successfully.".format(op.main_task.identifier)
                )
        except ConductorAbort:
            op.set_state(OperationState.ABORTED)
            # N.B. A slot may be leaked here, but it does not matter because we
            # are aborting the execution.
            raise
        except ConductorError as ex:
            op.store_error(ex)
            op.set_state(OperationState.FAILED)
            error_occurred = True
            self._print_op_failed(op)

        if handle.slot is not None:
            self._available_slots.append(handle.slot)
        self._process_finished_op(op)

        return error_occurred and stop_on_first_error

    def _process_finished_op(self, finished_op: Operation) -> None:
        self._completed_ops.append(finished_op)
        finished_op.decrement_deps_of_waiting_on()
        for dep_of in finished_op.deps_of:
            if dep_of.waiting_on > 0:
                continue
            self._ready_to_run.enqueue_op(dep_of)

    def _report_execution_results(self, plan: ExecutionPlan, elapsed_time: float):
        all_succeeded = all(map(lambda op: op.succeeded(), self._completed_ops))
        main_task_executed = any(
            [
                op.main_task is not None
                and op.main_task.identifier == plan.task_to_run.identifier
                for op in self._completed_ops
            ]
        )

        # We did not run any ops, so the task we wanted to run must have been
        # cached.
        main_task_cached = len(self._completed_ops) == 0 and any(
            [
                task.identifier == plan.task_to_run.identifier
                for task in plan.cached_tasks
            ]
        )

        # Print the final execution result (succeeded or failed).
        if all_succeeded and (main_task_executed or main_task_cached):
            if not self._silent:
                print()
                print_bold(
                    "✨ Done! {}".format(self._get_elapsed_time_string(elapsed_time))
                )

        else:
            # At least one task must have failed.
            failed_task_ops: List[Operation] = []
            skipped_tasks: List[TaskIdentifier] = []
            for op in self._completed_ops:
                if op.main_task is None:
                    continue
                if op.state == OperationState.SKIPPED:
                    skipped_tasks.append(op.main_task.identifier)
                elif op.state == OperationState.FAILED:
                    failed_task_ops.append(op)
            assert len(failed_task_ops) > 0
            if not self._silent:
                print()
                print_red(
                    "🔴 Task failed. {}".format(
                        self._get_elapsed_time_string(elapsed_time)
                    ),
                    bold=True,
                )
                print()
                print_bold("Failed task(s):")
                for failed in failed_task_ops:
                    assert failed.main_task is not None
                    print("  {}".format(failed.main_task.identifier))
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
                    print_bold("Skipped task(s) (one or more dependencies failed):")
                    for skipped in skipped_tasks:
                        print("  {}".format(skipped))
                    print()

            assert failed_task_ops[0].stored_error is not None
            raise failed_task_ops[0].stored_error

    def _print_op_failed(self, op: Operation):
        if op.main_task is None:
            return
        if self._silent:
            return
        print_red("✘ {} failed.".format(op.main_task.identifier))

    def _get_progress_string(self):
        return "({}/{})".format(str(self._num_tasks_dequeued), self._num_tasks_to_run)

    def _get_elapsed_time_string(self, elapsed: float):
        return "(Ran for {}.)".format(time_to_readable_string(elapsed))
