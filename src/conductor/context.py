import itertools
import os
import pathlib

from conductor.config import CONFIG_FILE_NAME
from conductor.errors import MissingProjectRoot
from conductor.parsing.task_index import TaskIndex
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType


class Context:
    def __init__(self, project_root):
        self._project_root = project_root
        self._task_index = TaskIndex(self._project_root)

    @classmethod
    def from_cwd(cls):
        """
        Creates a new Context by searching for the project root from the
        current working directory.
        """
        here = pathlib.Path(os.getcwd())
        for path in itertools.chain([here], here.parents):
            maybe_config_path = path / CONFIG_FILE_NAME
            if maybe_config_path.is_file():
                return cls(project_root=path)
        raise MissingProjectRoot()

    def run_tasks(self, task_selector):
        """
        Runs the task(s) specified by the given task selector.
        """
        # NOTE: Currently, we only consider task identifiers as valid task
        #       selectors.
        task_identifier = TaskIdentifier.from_str(
            task_selector,
            require_prefix=False,
        )
        self._task_index.load_transitive_closure(task_identifier)
        raw_task = self._task_index.get_task(task_identifier)
        task = TaskType.from_raw_task(task_identifier, raw_task)
        task.execute(project_root=self._project_root)
