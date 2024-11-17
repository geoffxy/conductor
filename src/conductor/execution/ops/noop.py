from typing import Optional

from conductor.context import Context
from conductor.execution.ops.operation import Operation
from conductor.execution.task_state import TaskState
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType, TaskExecutionHandle


class NoOp(Operation):
    """
    This operation exists to represent tasks that do not require any special
    execution but who should still be reported in the execution results.
    """

    def __init__(
        self, *, initial_state: TaskState, identifier: TaskIdentifier, task: TaskType
    ) -> None:
        super().__init__(initial_state)
        self._identifier = identifier
        self._task = task

    @property
    def associated_task(self) -> Optional[TaskType]:
        return self._task

    @property
    def main_task(self) -> Optional[TaskType]:
        return self._task

    def start_execution(self, ctx: Context, slot: Optional[int]) -> TaskExecutionHandle:
        return TaskExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: TaskExecutionHandle, ctx: Context) -> None:
        pass
