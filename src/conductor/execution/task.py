from typing import List, Optional

from conductor.execution.task_state import TaskState
from conductor.errors.base import ConductorError
from conductor.task_types.base import TaskType


class ExecutingTask:
    """
    Used to track metadata about a task during execution. See
    `execution.plan.ExecutionPlan` and `execution.executor.Executor`.
    """

    def __init__(self, task: TaskType, initial_state: TaskState):
        self._task = task
        self._state = initial_state
        self._stored_error: Optional[ConductorError] = None

        # A list of this task's dependencies (i.e., a list of tasks that must
        # execute successfully before this task can execute).
        self._exe_deps: List["ExecutingTask"] = []
        # The number of tasks that still need to complete before this task can
        # execute. This value is always less than or equal to
        # `len(self._exe_deps)`.
        self._waiting_on = 0

        # A list of tasks that have this task as a dependency (i.e., a list of
        # tasks that cannot execute until this task executes successfully).
        self._deps_of: List["ExecutingTask"] = []

    @property
    def task(self) -> TaskType:
        return self._task

    @property
    def state(self) -> TaskState:
        return self._state

    @property
    def exe_deps(self) -> List["ExecutingTask"]:
        return self._exe_deps

    @property
    def deps_of(self) -> List["ExecutingTask"]:
        return self._deps_of

    @property
    def stored_error(self) -> Optional[ConductorError]:
        return self._stored_error

    @property
    def waiting_on(self) -> int:
        return self._waiting_on

    def set_state(self, state: TaskState) -> None:
        self._state = state

    def add_exe_dep(self, exe_dep: "ExecutingTask") -> None:
        self._exe_deps.append(exe_dep)

    def add_dep_of(self, task: "ExecutingTask") -> None:
        self._deps_of.append(task)

    def store_error(self, error: ConductorError) -> None:
        self._stored_error = error

    def reset_waiting_on(self) -> None:
        self._waiting_on = len(self._exe_deps)

    def decrement_deps_of_waiting_on(self) -> None:
        for dep_of in self.deps_of:
            # pylint: disable=protected-access
            dep_of._decrement_waiting_on()

    def succeeded(self) -> bool:
        return (
            self.state == TaskState.SUCCEEDED
            or self.state == TaskState.SUCCEEDED_CACHED
        )

    def not_yet_executed(self) -> bool:
        return self.state == TaskState.QUEUED

    def exe_deps_succeeded(self) -> bool:
        """Returns true iff all dependent tasks have executed successfully."""
        return all(map(lambda task: task.succeeded(), self.exe_deps))

    def _decrement_waiting_on(self) -> None:
        assert self._waiting_on > 0
        self._waiting_on -= 1
