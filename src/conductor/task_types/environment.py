import pathlib
from typing import Optional, TYPE_CHECKING, Sequence, List

from conductor.task_identifier import TaskIdentifier
from .base import TaskType
from conductor.errors import InternalError, EnvExtraFilesNotRelative

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
        extra_files: Sequence[str],
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

        # Validate the extra files.
        self._extra_files = []
        for file_path_str in extra_files:
            file_path = pathlib.Path(file_path_str)
            if file_path.is_absolute():
                raise EnvExtraFilesNotRelative(env_name=identifier.name)
            self._extra_files.append(file_path)

    @property
    def start(self) -> Optional[str]:
        return self._start

    @property
    def stop(self) -> Optional[str]:
        return self._stop

    @property
    def connect_config(self) -> str:
        return self._connect_config

    @property
    def extra_files(self) -> List[pathlib.Path]:
        return self._extra_files

    def __repr__(self) -> str:
        # To reduce verbosity, we do not print out the other properties.
        return super().__repr__() + ")"

    def get_output_path(self, ctx: "c.Context") -> Optional[pathlib.Path]:
        # This task does not have any outputs.
        return None
