import itertools
import os
import pathlib

from conductor.config import CONFIG_FILE_NAME
from conductor.errors import MissingProjectRoot
from conductor.parsing.task_index import TaskIndex


class Context:
    """
    Represents an execution context, storing all the relevant state needed to
    carry out Conductor's functionality.
    """

    def __init__(self, project_root: pathlib.Path):
        self._project_root = project_root
        self._task_index = TaskIndex(self._project_root)
        self._run_again = False

    @classmethod
    def from_cwd(cls) -> "Context":
        """
        Creates a new `Context` by searching for the project root from the
        current working directory.
        """
        here = pathlib.Path(os.getcwd())
        for path in itertools.chain([here], here.parents):
            maybe_config_path = path / CONFIG_FILE_NAME
            if maybe_config_path.is_file():
                return cls(project_root=path)
        raise MissingProjectRoot()

    def set_run_again(self, again: bool) -> "Context":
        self._run_again = again
        return self

    @property
    def project_root(self) -> pathlib.Path:
        return self._project_root

    @property
    def task_index(self) -> TaskIndex:
        return self._task_index

    @property
    def run_again(self) -> bool:
        return self._run_again
