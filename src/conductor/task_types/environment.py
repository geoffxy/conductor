import pathlib
from typing import Optional, TYPE_CHECKING, Sequence

from conductor.task_identifier import TaskIdentifier
from .base import TaskType
from conductor.errors import InternalError

if TYPE_CHECKING:
    import conductor.context as c


class Environment(TaskType):
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        start: Optional[str],
        stop: Optional[str],
        connect_config: str,
        # Note that `deps` is supposed to be an empty sequence.
        deps: Sequence[TaskIdentifier],
    ):
        if len(deps) > 0:
            # This is an internal error because we perform validation earlier.
            raise InternalError(
                details=f"Environment '{str(identifier)}' cannot have dependencies."
            )

        super().__init__(identifier=identifier, cond_file_path=cond_file_path, deps=[])
        self._start = start
        self._stop = stop
        self._connect_config = connect_config

    @property
    def start(self) -> Optional[str]:
        return self._start

    @property
    def stop(self) -> Optional[str]:
        return self._stop

    @property
    def connect_config(self) -> str:
        return self._connect_config

    def __repr__(self) -> str:
        # To reduce verbosity, we do not print out the other properties.
        return super().__repr__() + ")"

    def get_output_path(self, ctx: "c.Context") -> Optional[pathlib.Path]:
        # This task does not have any outputs.
        return None
