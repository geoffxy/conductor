import pathlib
from typing import Sequence, Optional

import conductor.context as c  # pylint: disable=unused-import
from conductor.task_identifier import TaskIdentifier
from .base import TaskExecutionHandle, TaskType


class Group(TaskType):
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
    ):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps
        )

    def __repr__(self) -> str:
        return super().__repr__() + ")"

    def start_execution(
        self, ctx: "c.Context", slot: Optional[int]
    ) -> TaskExecutionHandle:
        # This task provides an "alias" for a group of other tasks (its
        # dependencies). As a result, it is a no-op.
        return TaskExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: "TaskExecutionHandle", ctx: "c.Context") -> None:
        # Nothing special needs to be done here.
        pass

    def get_output_path(self, ctx: "c.Context") -> Optional[pathlib.Path]:
        # This task does not have any outputs.
        return None
