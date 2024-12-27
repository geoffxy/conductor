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
        start: Optional[str],
        stop: Optional[str],
        host: str,
        user: str,
    ):
        super().__init__(identifier=identifier, cond_file_path=cond_file_path, deps=[])
        self._start = start
        self._stop = stop
        self._host = host
        self._user = user

    def __repr__(self) -> str:
        # To reduce verbosity, we do not print out the other properties.
        return super().__repr__() + ")"

    def get_output_path(self, ctx: "c.Context") -> Optional[pathlib.Path]:
        # This task does not have any outputs.
        return None
