import itertools
import os
import pathlib

from conductor.config import OUTPUT_DIR, TARGET_OUTPUT_DIR_SUFFIX


class TaskType:
    def __init__(self, identifier, cond_file_path, deps):
        self._identifier = identifier
        self._cond_file_path = cond_file_path
        # Ensure that the list of deps is immutable by making it a tuple)
        self._deps = tuple(deps)
        # Where this task's outputs should go (relative to the project root)
        self._output_path = pathlib.Path(
            OUTPUT_DIR,
            *self._identifier.path,
            self._identifier.name + TARGET_OUTPUT_DIR_SUFFIX,
        )

    def __repr__(self):
        return "".join(
            [
                self.__class__.__name__,
                "(identifier=",
                str(self._identifier),
            ]
        )

    @staticmethod
    def from_raw_task(identifier, raw_task, deps=[]):
        constructor = raw_task["_full_type"]
        del raw_task["name"]
        del raw_task["_full_type"]
        return constructor(identifier=identifier, deps=deps, **raw_task)

    @property
    def identifier(self):
        return self._identifier

    @property
    def deps(self):
        return self._deps

    def execute(self, project_root):
        raise NotImplementedError

    def get_and_prepare_output_path(self, project_root):
        """
        Returns a `pathlib.Path` object representing the absolute path to
        this task's outputs directory. If the output directory does not
        exist, this method will create it.
        """
        full_output_path = pathlib.Path(project_root) / self._output_path
        full_output_path.mkdir(parents=True, exist_ok=True)
        return full_output_path

    def get_deps_output_paths(self, project_root, task_index):
        """
        Returns a list of `pathlib.Path` objects that represent the output
        paths of this task's dependencies.
        """
        return [
            task_index.get_task(dep_identifier).get_and_prepare_output_path(
                project_root
            )
            for dep_identifier in self.deps
        ]

    def _get_working_path(self, project_root):
        return os.path.join(project_root, *self._identifier.path)
