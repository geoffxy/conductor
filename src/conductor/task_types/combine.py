import pathlib
from typing import Sequence

from conductor.errors import CombineDuplicateDepName
from conductor.task_identifier import TaskIdentifier
from .base import TaskType


class Combine(TaskType):
    """
    Copies the task outputs from this task's dependencies into this task's
    output directory.
    """

    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
    ):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps
        )

        # Make sure that the task dependencies do not have the same name. This
        # is because `combine()` will create subdirectories using each task's
        # name (not fully qualified identifier).
        task_names = set()
        for dep in deps:
            if dep.name in task_names:
                raise CombineDuplicateDepName(
                    task_identifier=identifier, task_name=dep.name
                )
            task_names.add(dep.name)

    def __repr__(self) -> str:
        return super().__repr__() + ")"
