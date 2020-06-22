import itertools
import os
import pathlib

from conductor.config import CONFIG_FILE_NAME
from conductor.errors import ConductorError, TaskNotFound
from conductor.parsing.task_loader import TaskLoader
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType
from conductor.user_code_utils import prevent_module_caching


class Context:
    def __init__(self, project_root):
        self._project_root = project_root
        self._task_loader = TaskLoader()

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
        raise ConductorError(
            "Could not locate your project's root. Did you add a {} file?"
            .format(CONFIG_FILE_NAME),
        )

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
        with prevent_module_caching():
            raw_tasks = self._task_loader.parse_cond_file(
                task_identifier.path_to_cond_file(),
            )
        if task_identifier.name not in raw_tasks:
            raise TaskNotFound(
                "Task '{}' not found.".format(str(task_identifier)),
            )
        task = TaskType.from_raw_task(
            task_identifier,
            raw_tasks[task_identifier.name],
        )
        print(task)
