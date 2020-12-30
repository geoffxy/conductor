import subprocess
import pathlib
from typing import Iterable

import conductor.context as c
from conductor.errors import TaskFailed, TaskNonZeroExit
from conductor.task_identifier import TaskIdentifier
from conductor.config import (
    OUTPUT_ENV_VARIABLE_NAME,
    DEPS_ENV_VARIABLE_NAME,
    DEPS_ENV_PATH_SEPARATOR,
)
from .base import TaskType


class RunCommand(TaskType):
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Iterable[TaskIdentifier],
        run: str,
    ):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps
        )
        self._run = run

    def __repr__(self) -> str:
        return "".join(
            [
                super().__repr__(),
                ", run=",
                self._run,
                ")",
            ]
        )

    def execute(self, ctx: "c.Context") -> None:
        try:
            process = subprocess.Popen(
                [self._run],
                shell=True,
                cwd=self._get_working_path(ctx),
                env={
                    OUTPUT_ENV_VARIABLE_NAME: str(
                        self.get_and_prepare_output_path(ctx)
                    ),
                    DEPS_ENV_VARIABLE_NAME: DEPS_ENV_PATH_SEPARATOR.join(
                        map(str, self.get_deps_output_paths(ctx))
                    ),
                },
            )
            process.wait()
            if process.returncode != 0:
                raise TaskNonZeroExit(
                    task_identifier=self.identifier, code=process.returncode
                )

        except OSError as ex:
            raise TaskFailed(task_identifier=self.identifier).add_extra_context(str(ex))


class RunExperiment(RunCommand):
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Iterable[TaskIdentifier],
        run: str,
    ):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps, run=run
        )

    def should_run(self, ctx: "c.Context") -> bool:
        """
        We use the presence of files in the output directory to determine
        whether or not we should run the experiment again.
        """
        output_path = self.get_and_prepare_output_path(ctx)
        # Returns false iff there is at least one file in the directory
        return not any(True for _ in output_path.iterdir())
