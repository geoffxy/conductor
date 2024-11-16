import pathlib
from typing import Optional, Sequence

from conductor.context import Context
from conductor.execution.ops.operation import Operation
from conductor.execution.task_state import TaskState
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskExecutionHandle, TaskType


class CombineOutputs(Operation):
    def __init__(
        self,
        *,
        initial_state: TaskState,
        task: TaskType,
        identifier: TaskIdentifier,
        output_path: pathlib.Path,
        deps_output_paths: Sequence[pathlib.Path],
    ) -> None:
        super().__init__(initial_state)
        self._identifier = identifier
        self._task = task
        self._output_path = output_path
        self._deps_output_paths = deps_output_paths

    @property
    def associated_task(self) -> Optional[TaskType]:
        return self._task

    @property
    def main_task(self) -> Optional[TaskType]:
        return self._task

    def start_execution(self, ctx: Context, slot: Optional[int]) -> TaskExecutionHandle:
        self._output_path.mkdir(parents=True, exist_ok=True)

        for dep_dir in self._deps_output_paths:
            if (
                not dep_dir.is_dir()
                # Checks if the directory is empty
                or not any(True for _ in dep_dir.iterdir())
            ):
                continue
            copy_into = self._output_path / dep_dir.name
            # The base data may be large, so we use symlinks to avoid copying.
            copy_into.symlink_to(dep_dir, target_is_directory=True)

        return TaskExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: TaskExecutionHandle, ctx: Context) -> None:
        # Nothing special needs to be done here.
        pass
