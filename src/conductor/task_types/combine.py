import pathlib
import shutil
from typing import Sequence, Optional

import conductor.context as c  # pylint: disable=unused-import
from conductor.errors import CombineDuplicateDepName
from conductor.task_identifier import TaskIdentifier
from .base import TaskType, TaskExecutionHandle


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

    def start_execution(
        self, ctx: "c.Context", slot: Optional[int]
    ) -> TaskExecutionHandle:
        output_path = self.get_output_path(ctx)
        assert output_path is not None

        for dep in self.deps:
            task = ctx.task_index.get_task(dep)
            task_output_dir = task.get_output_path(ctx)
            if (
                task_output_dir is None
                or not task_output_dir.is_dir()
                # Checks if the directory is empty
                or not any(True for _ in task_output_dir.iterdir())
            ):
                continue
            copy_into = output_path / dep.name
            shutil.copytree(task_output_dir, copy_into, dirs_exist_ok=True)

        return TaskExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: "TaskExecutionHandle", ctx: "c.Context") -> None:
        # Nothing special needs to be done here.
        pass
