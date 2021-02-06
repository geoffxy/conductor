import itertools
import pathlib
from typing import Optional

from conductor.config import CONFIG_FILE_NAME, OUTPUT_DIR, VERSION_INDEX_NAME
from conductor.errors import MissingProjectRoot, OutputDirTaken
from conductor.execution.version_index import VersionIndex
from conductor.parsing.task_index import TaskIndex
from conductor.utils.tee import TeeProcessor


class Context:
    """
    Represents an execution context, storing all the relevant state needed to
    carry out Conductor's functionality.
    """

    def __init__(self, project_root: pathlib.Path):
        self._project_root = project_root
        self._task_index = TaskIndex(self._project_root)
        self._output_path = project_root / OUTPUT_DIR
        self._ensure_output_dir_exists()

        self._version_index = VersionIndex.create_or_load(
            pathlib.Path(self.output_path, VERSION_INDEX_NAME)
        )

        # We lazily initialize the TeeProcessor because it may not always be needed.
        self._tee_processor: Optional[TeeProcessor] = None

    @classmethod
    def from_cwd(cls) -> "Context":
        """
        Creates a new `Context` by searching for the project root from the
        current working directory.
        """
        here = pathlib.Path.cwd()
        for path in itertools.chain([here], here.parents):
            maybe_config_path = path / CONFIG_FILE_NAME
            if maybe_config_path.is_file():
                return cls(project_root=path)
        raise MissingProjectRoot()

    @property
    def project_root(self) -> pathlib.Path:
        return self._project_root

    @property
    def output_path(self) -> pathlib.Path:
        return self._output_path

    @property
    def task_index(self) -> TaskIndex:
        return self._task_index

    @property
    def version_index(self) -> VersionIndex:
        return self._version_index

    @property
    def tee_processor(self) -> TeeProcessor:
        if self._tee_processor is None:
            self._tee_processor = TeeProcessor()
        return self._tee_processor

    def _ensure_output_dir_exists(self) -> None:
        self.output_path.mkdir(exist_ok=True)
        if not self.output_path.is_dir():
            raise OutputDirTaken()
