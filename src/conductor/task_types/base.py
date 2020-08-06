import itertools
import os
import pathlib

from conductor.config import OUTPUT_DIR


class TaskType:
    def __init__(self, identifier, cond_file_path):
        self._identifier = identifier
        self._cond_file_path = cond_file_path

    def __repr__(self):
        return "".join([
            self.__class__.__name__,
            "(identifier=",
            str(self._identifier),
        ])

    @staticmethod
    def from_raw_task(identifier, raw_task):
        constructor = raw_task["_full_type"]
        del raw_task["name"]
        del raw_task["_full_type"]
        # TODO: Handle dependencies properly
        del raw_task["deps"]
        return constructor(identifier=identifier, **raw_task)

    @property
    def identifier(self):
        return self._identifier

    def execute(self, project_root):
        raise NotImplementedError

    def _get_and_prepare_output_path(self, project_root):
        out_path = pathlib.Path(project_root)
        for component in itertools.chain([OUTPUT_DIR], self._identifier.path):
            out_path = out_path / component
            out_path.mkdir(exist_ok=True)
        return str(out_path)

    def _get_working_path(self, project_root):
        return os.path.join(project_root, *self._identifier.path)
