import pathlib
from typing import Optional

import conductor.context as c  # pylint: disable=unused-import
from conductor.task_identifier import TaskIdentifier
from .base import TaskExecutionHandle, TaskType


class Environment(TaskType):
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
    ):
        super().__init__(identifier=identifier, cond_file_path=cond_file_path, deps=[])

    def __repr__(self) -> str:
        return super().__repr__() + ")"

    def start_execution(
        self, ctx: "c.Context", slot: Optional[int]
    ) -> TaskExecutionHandle:
        # No-op.
        return TaskExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: "TaskExecutionHandle", ctx: "c.Context") -> None:
        # Nothing special needs to be done here.
        pass

    def get_output_path(self, ctx: "c.Context") -> Optional[pathlib.Path]:
        # This task does not have any outputs.
        return None
