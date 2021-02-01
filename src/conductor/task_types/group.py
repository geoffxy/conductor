import pathlib
from typing import Sequence

import conductor.context as c  # pylint: disable=unused-import
from conductor.task_identifier import TaskIdentifier
from .base import TaskType


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

    def execute(self, ctx: "c.Context"):
        # This task provides an "alias" for a group of other tasks (its
        # dependencies). As a result, it is a no-op.
        pass
