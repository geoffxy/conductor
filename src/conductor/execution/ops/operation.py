from typing import List, Optional

from conductor.context import Context
from conductor.errors.base import ConductorError
from conductor.execution.task_state import TaskState
from conductor.task_types.base import TaskType, TaskExecutionHandle


class Operation:
    """
    Represents a physical unit of work to run. Conductor task types are
    converted to operations for execution.
    """

    # NOTE: TaskState will be renamed to OperationState after the refactor.

    def __init__(self, initial_state: TaskState) -> None:
        self._state = initial_state
        self._stored_error: Optional[ConductorError] = None

        # A list of this operation's dependencies (i.e., a list of tasks that must
        # execute successfully before this task can execute).
        self._exe_deps: List["Operation"] = []
        # The number of operations that still need to complete before this
        # operation can execute. This value is always less than or equal to
        # `len(self._exe_deps)`.
        self._waiting_on = 0

        # A list of operations that have this operation as a dependency (i.e., a
        # list of tasks that cannot execute until this operation executes
        # successfully).
        self._deps_of: List["Operation"] = []

    @property
    def associated_task(self) -> Optional[TaskType]:
        """
        The task that is responsible for creating this operation, if any.
        """
        return None

    # Execution-related methods.

    def start_execution(self, ctx: Context, slot: Optional[int]) -> TaskExecutionHandle:
        raise NotImplementedError

    def finish_execution(self, handle: TaskExecutionHandle, ctx: Context) -> None:
        raise NotImplementedError

    # Execution state methods.

    @property
    def state(self) -> TaskState:
        return self._state

    @property
    def exe_deps(self) -> List["Operation"]:
        return self._exe_deps

    @property
    def deps_of(self) -> List["Operation"]:
        return self._deps_of

    @property
    def stored_error(self) -> Optional[ConductorError]:
        return self._stored_error

    @property
    def waiting_on(self) -> int:
        return self._waiting_on

    def set_state(self, state: TaskState) -> None:
        self._state = state

    def add_exe_dep(self, exe_dep: "Operation") -> None:
        self._exe_deps.append(exe_dep)

    def add_dep_of(self, task: "Operation") -> None:
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
        """
        Returns true iff all dependent operations have executed successfully.
        """
        return all(map(lambda task: task.succeeded(), self.exe_deps))

    def _decrement_waiting_on(self) -> None:
        assert self._waiting_on > 0
        self._waiting_on -= 1
