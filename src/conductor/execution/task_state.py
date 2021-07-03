import enum
from typing import List, Optional

from conductor.errors.base import ConductorError
from conductor.task_types.base import TaskType


class TaskState(enum.Enum):
    # The task is queued to be executed
    QUEUED = 0

    # Currently executing the task's dependencies
    EXECUTING_DEPS = 1

    # Skipped executing this task because one or more of its dependencies
    # failed to execute successfully.
    SKIPPED = 1

    # The task was executed successfully.
    SUCCEEDED = 2

    # The task was executed successfully at some prior point in time and its
    # results were cached. As a result, the task was not executed as a part of
    # this Conductor invocation.
    SUCCEEDED_CACHED = 3

    # The task failed when it was executed (non-zero exit code).
    FAILED = 4


class ExecutingTask:
    """
    Used to track metadata about a task during execution. See
    `execution.plan.ExecutionPlan`.
    """

    def __init__(self, task: TaskType):
        self._task = task
        self._state = TaskState.QUEUED
        self._deps: List["ExecutingTask"] = []
        self._stored_error: Optional[ConductorError] = None

    @property
    def task(self) -> TaskType:
        return self._task

    @property
    def state(self) -> TaskState:
        return self._state

    @property
    def deps(self) -> List["ExecutingTask"]:
        return self._deps

    @property
    def stored_error(self) -> Optional[ConductorError]:
        return self._stored_error

    def set_state(self, state: TaskState) -> None:
        self._state = state

    def add_dep(self, dep: "ExecutingTask") -> None:
        self._deps.append(dep)

    def succeeded(self) -> bool:
        return (
            self.state == TaskState.SUCCEEDED
            or self.state == TaskState.SUCCEEDED_CACHED
        )

    def not_yet_executed(self) -> bool:
        return self.state == TaskState.QUEUED or self.state == TaskState.EXECUTING_DEPS

    def store_error(self, error: ConductorError) -> None:
        self._stored_error = error
