import pathlib
import subprocess
from typing import Optional

from conductor.context import Context
from conductor.errors import MissingEnvSupport, EnvShutdownFailed
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.operation_state import OperationState
from conductor.execution.ops.operation import Operation


class ShutdownRemoteEnv(Operation):
    def __init__(
        self,
        initial_state: OperationState,
        env_name: str,
        shutdown_runnable: Optional[str],
        working_path: pathlib.Path,
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._shutdown_runnable = shutdown_runnable
        self._working_path = working_path

    def start_progress_message(self) -> Optional[str]:
        return f"Shutting down environment '{self._env_name}'..."

    def finish_progress_message(self) -> Optional[str]:
        return f"Environment '{self._env_name}' has successfully shutdown."

    def error_progress_message(self) -> Optional[str]:
        return f"Failed to shutdown environment '{self._env_name}'."

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        if ctx.envs is None:
            raise MissingEnvSupport()

        ctx.envs.shutdown_remote_env(self._env_name)
        self._invoke_shutdown_runnable()

        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass

    def _invoke_shutdown_runnable(self) -> None:
        if self._shutdown_runnable is None:
            return

        try:
            start_result = subprocess.run(
                [self._shutdown_runnable],
                cwd=self._working_path,
                shell=True,
                start_new_session=True,
                check=False,
                capture_output=True,
            )
            if start_result.returncode != 0:
                stdout_str = start_result.stdout.decode("utf-8")
                stderr_str = start_result.stderr.decode("utf-8")
                raise EnvShutdownFailed(env_name=self._env_name).add_extra_context(
                    f"stdout: {stdout_str}\nstderr: {stderr_str}"
                )
        except OSError as ex:
            raise EnvShutdownFailed(env_name=self._env_name).add_extra_context(
                str(ex)
            ) from ex
