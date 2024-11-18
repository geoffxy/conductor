import os
import pathlib
import signal
import subprocess
import sys
from typing import Optional, Sequence

from conductor.config import (
    OUTPUT_ENV_VARIABLE_NAME,
    DEPS_ENV_VARIABLE_NAME,
    DEPS_ENV_PATH_SEPARATOR,
    TASK_NAME_ENV_VARIABLE_NAME,
    STDOUT_LOG_FILE,
    STDERR_LOG_FILE,
    EXP_ARGS_JSON_FILE_NAME,
    EXP_OPTION_JSON_FILE_NAME,
    SLOT_ENV_VARIABLE_NAME,
)
from conductor.context import Context
from conductor.errors import (
    TaskFailed,
    TaskNonZeroExit,
    ConductorAbort,
)
from conductor.execution.ops.operation import Operation
from conductor.execution.operation_state import OperationState
from conductor.execution.version_index import Version
from conductor.task_types.base import TaskExecutionHandle, TaskType
from conductor.task_identifier import TaskIdentifier
from conductor.utils.output_handler import RecordType, OutputHandler
from conductor.utils.run_arguments import RunArguments
from conductor.utils.run_options import RunOptions


class RunTaskExecutable(Operation):
    def __init__(
        self,
        *,
        initial_state: OperationState,
        identifier: TaskIdentifier,
        task: TaskType,
        run: str,
        args: RunArguments,
        options: RunOptions,
        working_path: pathlib.Path,
        output_path: pathlib.Path,
        deps_output_paths: Sequence[pathlib.Path],
        record_output: bool,
        version_to_record: Optional[Version],
        serialize_args_options: bool,
        parallelizable: bool,
    ) -> None:
        super().__init__(initial_state)
        self._identifier = identifier
        self._task = task
        self._args = args
        self._options = options
        self._run = " ".join(
            [run, self._args.serialize_cmdline(), self._options.serialize_cmdline()]
        )
        self._working_path = working_path
        self._output_path = output_path
        self._deps_output_paths = deps_output_paths
        self._record_output = record_output
        self._version_to_record = version_to_record
        self._serialize_args_options = serialize_args_options
        self._parallelizable = parallelizable

    @property
    def associated_task(self) -> Optional[TaskType]:
        return self._task

    @property
    def main_task(self) -> Optional[TaskType]:
        return self._task

    def start_execution(self, ctx: Context, slot: Optional[int]) -> TaskExecutionHandle:
        try:
            self._output_path.mkdir(parents=True, exist_ok=True)

            env_vars = {
                **os.environ,
                OUTPUT_ENV_VARIABLE_NAME: str(self._output_path),
                DEPS_ENV_VARIABLE_NAME: DEPS_ENV_PATH_SEPARATOR.join(
                    map(str, self._deps_output_paths)
                ),
                TASK_NAME_ENV_VARIABLE_NAME: self._identifier.name,
            }
            if slot is not None:
                env_vars[SLOT_ENV_VARIABLE_NAME] = str(slot)

            if self._record_output:
                if slot is None:
                    record_type = RecordType.Teed
                else:
                    record_type = RecordType.OnlyLogged
            else:
                record_type = RecordType.NotRecorded

            stdout_output = OutputHandler(
                self._output_path / STDOUT_LOG_FILE, record_type
            )
            stderr_output = OutputHandler(
                self._output_path / STDERR_LOG_FILE, record_type
            )

            process = subprocess.Popen(
                [self._run],
                shell=True,
                cwd=self._working_path,
                executable="/bin/bash",
                stdout=stdout_output.popen_arg(),
                stderr=stderr_output.popen_arg(),
                env=env_vars,
                start_new_session=True,
            )

            stdout_output.maybe_tee(process.stdout, sys.stdout, ctx)
            stderr_output.maybe_tee(process.stderr, sys.stderr, ctx)

            handle = TaskExecutionHandle.from_async_process(pid=process.pid)
            handle.stdout = stdout_output
            handle.stderr = stderr_output
            return handle

        except ConductorAbort:
            # Send SIGTERM to the entire process group (i.e., the subprocess
            # and its child processes).
            if process is not None:
                group_id = os.getpgid(process.pid)
                if group_id >= 0:
                    os.killpg(group_id, signal.SIGTERM)
            if self._record_output:
                ctx.tee_processor.shutdown()
            raise

        except OSError as ex:
            raise TaskFailed(task_identifier=self._identifier).add_extra_context(
                str(ex)
            )

    def finish_execution(self, handle: "TaskExecutionHandle", ctx: Context) -> None:
        assert handle.stdout is not None
        assert handle.stderr is not None
        handle.stdout.finish()
        handle.stderr.finish()

        assert handle.returncode is not None
        if handle.returncode != 0:
            raise TaskNonZeroExit(
                task_identifier=self._identifier, code=handle.returncode
            )

        if self._serialize_args_options:
            if not self._args.empty():
                self._args.serialize_json(self._output_path / EXP_ARGS_JSON_FILE_NAME)
            if not self._options.empty():
                self._options.serialize_json(
                    self._output_path / EXP_OPTION_JSON_FILE_NAME
                )

        if self._version_to_record is not None:
            ctx.version_index.insert_output_version(
                self._identifier, self._version_to_record
            )
            ctx.version_index.commit_changes()

    @property
    def parallelizable(self) -> bool:
        return self._parallelizable
