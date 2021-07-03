from typing import List, Optional

from conductor.execution.task_state import TaskState
from conductor.errors.base import ConductorError
from conductor.task_types.base import TaskType


class ExecutingTask:
    """
    Used to track metadata about a task during execution. See
    `execution.plan.ExecutionPlan`. This class is essentially a light wrapper
    around a `TaskType` instance.
    """

    def __init__(self, task: TaskType):
        self._task = task
        self._state = TaskState.QUEUED
        self._exe_deps: List["ExecutingTask"] = []
        self._stored_error: Optional[ConductorError] = None

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
    def stored_error(self) -> Optional[ConductorError]:
        return self._stored_error

    def set_state(self, state: TaskState) -> None:
        self._state = state

    def add_exe_dep(self, exe_dep: "ExecutingTask") -> None:
        self._exe_deps.append(exe_dep)

    def store_error(self, error: ConductorError) -> None:
        self._stored_error = error

    def succeeded(self) -> bool:
        return (
            self.state == TaskState.SUCCEEDED
            or self.state == TaskState.SUCCEEDED_CACHED
        )

    def not_yet_executed(self) -> bool:
        return self.state == TaskState.QUEUED or self.state == TaskState.EXECUTING_DEPS

    def exe_deps_succeeded(self) -> bool:
        """Returns true iff all dependent tasks have executed successfully."""
        return all(map(lambda task: task.succeeded(), self.exe_deps))
