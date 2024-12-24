import pathlib
from typing import Optional, TYPE_CHECKING

from conductor.task_identifier import TaskIdentifier
from .base import TaskType

if TYPE_CHECKING:
    import conductor.context as c


class Environment(TaskType):
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        create: str,
        start: str,
        stop: str,
        destroy: str,
        project_root: Optional[str],
        mirrored_files: bool,
    ):
        super().__init__(identifier=identifier, cond_file_path=cond_file_path, deps=[])
        self._create = create
        self._start = start
        self._stop = stop
        self._destroy = destroy
        self._project_root = project_root
        self._mirrored_files = mirrored_files

    def __repr__(self) -> str:
        # To reduce verbosity, we do not print out the other properties.
        return super().__repr__() + ")"

    def get_output_path(self, ctx: "c.Context") -> Optional[pathlib.Path]:
        # This task does not have any outputs.
        return None
