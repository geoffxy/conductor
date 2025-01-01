import pathlib
import subprocess
from typing import Optional

from conductor.context import Context
from conductor.errors import MissingEnvSupport, EnvStartFailed
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.operation_state import OperationState
from conductor.execution.ops.operation import Operation


class StartRemoteEnv(Operation):
    def __init__(
        self,
        initial_state: OperationState,
        env_name: str,
        start_runnable: Optional[str],
        working_path: pathlib.Path,
        # NOTE: We should find an more elegant way to specify host details. EC2
        # machines will not have a fixed host value.
        remote_host: str,
        remote_user: str,
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._start_runnable = start_runnable
        self._working_path = working_path
        self._remote_host = remote_host
        self._remote_user = remote_user

    def start_progress_message(self) -> Optional[str]:
        return f"Starting environment '{self._env_name}'..."

    def finish_progress_message(self) -> Optional[str]:
        return f"Environment '{self._env_name}' has successfully started."

    def error_progress_message(self) -> Optional[str]:
        return f"Failed to start environment '{self._env_name}'."

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        if ctx.envs is None:
            raise MissingEnvSupport()

        self._invoke_start_runnable()
        ctx.envs.start_remote_env(
            name=self._env_name, host=self._remote_host, user=self._remote_user
        )

        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass

    def _invoke_start_runnable(self) -> None:
        if self._start_runnable is None:
            return

        try:
            start_result = subprocess.run(
                [self._start_runnable],
                cwd=self._working_path,
                shell=True,
                start_new_session=True,
                check=False,
                capture_output=True,
            )
            if start_result.returncode != 0:
                stdout_str = start_result.stdout.decode("utf-8")
                stderr_str = start_result.stderr.decode("utf-8")
                raise EnvStartFailed(env_name=self._env_name).add_extra_context(
                    f"stdout: {stdout_str}\nstderr: {stderr_str}"
                )
        except OSError as ex:
            raise EnvStartFailed(env_name=self._env_name).add_extra_context(
                str(ex)
            ) from ex
