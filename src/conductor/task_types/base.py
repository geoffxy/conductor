import itertools
import os
import pathlib
from typing import Iterable, Dict

import conductor.context as c
from conductor.config import OUTPUT_DIR, TARGET_OUTPUT_DIR_SUFFIX
from conductor.task_identifier import TaskIdentifier


class TaskType:
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Iterable[TaskIdentifier],
    ):
        self._identifier = identifier
        self._cond_file_path = cond_file_path
        # Ensure that the list of deps is immutable by making it a tuple)
        self._deps = tuple(deps)
        # Where this task's outputs should go (relative to the project root)
        self._output_path = pathlib.Path(
            OUTPUT_DIR,
            self._identifier.path,
            self._identifier.name + TARGET_OUTPUT_DIR_SUFFIX,
        )

    def __repr__(self) -> str:
        return "".join(
            [
                self.__class__.__name__,
                "(identifier=",
                str(self._identifier),
            ]
        )

    @staticmethod
    def from_raw_task(
        identifier: TaskIdentifier, raw_task: Dict, deps=[]
    ) -> "TaskType":
        constructor = raw_task["_full_type"]
        del raw_task["name"]
        del raw_task["_full_type"]
        return constructor(identifier=identifier, deps=deps, **raw_task)

    @property
    def identifier(self) -> TaskIdentifier:
        return self._identifier

    @property
    def deps(self) -> Iterable[TaskIdentifier]:
        return self._deps

    def execute(self, ctx: "c.Context"):
        raise NotImplementedError

    def get_and_prepare_output_path(self, ctx: "c.Context") -> pathlib.Path:
        """
        Returns the absolute path to this task's outputs directory. If the
        output directory does not exist, this method will create it.
        """
        full_output_path = ctx.project_root / self._output_path
        full_output_path.mkdir(parents=True, exist_ok=True)
        return full_output_path

    def get_deps_output_paths(self, ctx: "c.Context") -> Iterable[pathlib.Path]:
        """
        Returns a list of `pathlib.Path` objects that represent the output
        paths of this task's dependencies.
        """
        return [
            ctx.task_index.get_task(dep_identifier).get_and_prepare_output_path(ctx)
            for dep_identifier in self.deps
        ]

    def _get_working_path(self, ctx: "c.Context") -> pathlib.Path:
        return pathlib.Path(ctx.project_root, self._identifier.path)
