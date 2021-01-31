import pathlib
import shutil
from typing import Iterable

import conductor.context as c  # pylint: disable=unused-import
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
        deps: Iterable[TaskIdentifier],
    ):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps
        )

    def __repr__(self) -> str:
        return super().__repr__() + ")"

    def execute(self, ctx: "c.Context"):
        output_path = self.get_output_path(ctx, create_new=True)
        assert output_path is not None

        for dep in self.deps:
            task = ctx.task_index.get_task(dep)
            task_output_dir = task.get_output_path(ctx)
            if task_output_dir is None or not task_output_dir.exists():
                continue
            shutil.copytree(task_output_dir, output_path, dirs_exist_ok=True)
