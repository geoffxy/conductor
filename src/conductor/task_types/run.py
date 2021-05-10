import subprocess
import pathlib
import os
import signal
import sys
from typing import Sequence, Optional

import conductor.context as c  # pylint: disable=unused-import
import conductor.filename as f
from conductor.errors import TaskFailed, TaskNonZeroExit, ConductorAbort
from conductor.task_identifier import TaskIdentifier
from conductor.config import (
    OUTPUT_ENV_VARIABLE_NAME,
    DEPS_ENV_VARIABLE_NAME,
    DEPS_ENV_PATH_SEPARATOR,
    TASK_NAME_ENV_VARIABLE_NAME,
    STDOUT_LOG_FILE,
    STDERR_LOG_FILE,
    EXP_ARGS_JSON_FILE_NAME,
    EXP_OPTION_JSON_FILE_NAME,
)
from conductor.utils.experiment_arguments import ExperimentArguments
from conductor.utils.experiment_options import ExperimentOptions
from .base import TaskType


class _RunSubprocess(TaskType):
    """
    An abstract base class representing tasks that launch a subprocess.
    """

    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
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

    @property
    def record_output(self) -> bool:
        """
        If set to True, this task's output on stdout and stderr will be
        recorded and saved to files in the task's output directory.
        """
        raise NotImplementedError

    def execute(self, ctx: "c.Context") -> None:
        try:
            output_path = self.get_output_path(ctx, create_new=True)
            assert output_path is not None
            output_path.mkdir(parents=True, exist_ok=True)
            process = subprocess.Popen(
                [self._run],
                shell=True,
                cwd=self._get_working_path(ctx),
                executable="/bin/bash",
                stdout=subprocess.PIPE if self.record_output else None,
                stderr=subprocess.PIPE if self.record_output else None,
                env={
                    **os.environ,
                    OUTPUT_ENV_VARIABLE_NAME: str(output_path),
                    DEPS_ENV_VARIABLE_NAME: DEPS_ENV_PATH_SEPARATOR.join(
                        map(str, self.get_deps_output_paths(ctx))
                    ),
                    TASK_NAME_ENV_VARIABLE_NAME: self.identifier.name,
                },
                start_new_session=True,
            )
            if self.record_output:
                assert process.stdout is not None
                assert process.stderr is not None
                stdout_tee = ctx.tee_processor.tee_pipe(
                    process.stdout, sys.stdout, output_path / STDOUT_LOG_FILE
                )
                stderr_tee = ctx.tee_processor.tee_pipe(
                    process.stderr, sys.stderr, output_path / STDERR_LOG_FILE
                )
            process.wait()
            if self.record_output:
                stdout_tee.result()
                stderr_tee.result()
            if process.returncode != 0:
                raise TaskNonZeroExit(
                    task_identifier=self.identifier, code=process.returncode
                )

        except ConductorAbort:
            # Send SIGTERM to the entire process group (i.e., the subprocess
            # and its child processes).
            if process is not None:
                group_id = os.getpgid(process.pid)
                if group_id >= 0:
                    os.killpg(group_id, signal.SIGTERM)
            if self.record_output:
                ctx.tee_processor.shutdown()
            raise

        except OSError as ex:
            raise TaskFailed(task_identifier=self.identifier).add_extra_context(str(ex))


class RunCommand(_RunSubprocess):
    """
    Represents the `run_command()` task type.

    Runs a command using `bash`. The task's standard out and error are not
    recorded. The task's outputs are not archivable either.
    """

    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
        run: str,
    ):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps, run=run
        )

    @property
    def record_output(self) -> bool:
        return False


class RunExperiment(_RunSubprocess):
    """
    Represents the `run_experiment()` task type.

    Runs a command using `bash`. The task's standard out and error are
    recorded. The task's outputs are placed in a timestamped directory and
    are archivable.
    """

    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
        run: str,
        args: list,
        options: dict,
    ):
        self._args = ExperimentArguments.from_raw(identifier, args)
        self._options = ExperimentOptions.from_raw(identifier, options)
        super().__init__(
            identifier=identifier,
            cond_file_path=cond_file_path,
            deps=deps,
            run=" ".join(
                [run, self._args.serialize_cmdline(), self._options.serialize_cmdline()]
            ),
        )

    @property
    def archivable(self) -> bool:
        return True

    @property
    def record_output(self) -> bool:
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

    def execute(self, ctx: "c.Context") -> None:
        super().execute(ctx)
        # Record the experiment args and options, if any were specified.
        if self._args.empty() and self._options.empty():
            return

        output_path = self.get_output_path(ctx)
        assert output_path is not None

        if not self._args.empty():
            self._args.serialize_json(output_path / EXP_ARGS_JSON_FILE_NAME)
        if not self._options.empty():
            self._options.serialize_json(output_path / EXP_OPTION_JSON_FILE_NAME)
