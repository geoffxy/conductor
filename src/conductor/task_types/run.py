import subprocess
import pathlib
from typing import Iterable, Optional

import conductor.context as c  # pylint: disable=unused-import
import conductor.filename as f
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
            output_path = self.get_output_path(ctx, create_new=True)
            assert output_path is not None
            output_path.mkdir(parents=True, exist_ok=True)
            process = subprocess.Popen(
                [self._run],
                shell=True,
                cwd=self._get_working_path(ctx),
                env={
                    OUTPUT_ENV_VARIABLE_NAME: str(output_path),
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

    @property
    def archivable(self) -> bool:
        return True

    def get_output_path(
        self, ctx: "c.Context", create_new: bool = False
    ) -> Optional[pathlib.Path]:
        unversioned_path = super().get_output_path(ctx, create_new)
        assert unversioned_path is not None

        if not create_new:
            latest = ctx.version_index.get_latest_output_version(self.identifier)
            if latest is None:
                return None
            return unversioned_path.with_name(
                f.task_output_dir(self.identifier, version=latest)
            )

        return unversioned_path.with_name(
            f.task_output_dir(
                self.identifier,
                version=ctx.version_index.generate_new_output_version(self.identifier),
            )
        )

    def should_run(self, ctx: "c.Context") -> bool:
        """
        We use the presence of files in the output directory to determine
        whether or not we should run the experiment again.
        """
        output_path = self.get_output_path(ctx)
        # Returns true iff the output directory does not exist or it is empty
        return output_path is None or not any(True for _ in output_path.iterdir())
