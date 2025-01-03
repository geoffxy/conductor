import pathlib
import subprocess
import tomli
from typing import Optional, Any, Dict

from conductor.context import Context
from conductor.errors import (
    MissingEnvSupport,
    EnvStartFailed,
    EnvConfigInvalid,
    EnvConfigScriptFailed,
)
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
        connect_config_runnable: str,
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._start_runnable = start_runnable
        self._working_path = working_path
        self._connect_config_runnable = connect_config_runnable

    def start_progress_message(self) -> Optional[str]:
        return f"Starting environment '{self._env_name}'..."

    def error_progress_message(self) -> Optional[str]:
        return f"Failed to start environment '{self._env_name}'."

    @property
    def env_name(self) -> str:
        return self._env_name

    def clone_without_deps(self) -> "StartRemoteEnv":
        return StartRemoteEnv(
            initial_state=self._state,
            env_name=self._env_name,
            start_runnable=self._start_runnable,
            working_path=self._working_path,
            connect_config_runnable=self._connect_config_runnable,
        )

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        if ctx.envs is None:
            raise MissingEnvSupport()

        self._invoke_start_runnable()

        connect_config = self._get_raw_connect_config()
        host = connect_config["host"]
        user = connect_config["user"]
        del connect_config["host"]
        del connect_config["user"]

        ctx.envs.start_remote_env(
            name=self._env_name, host=host, user=user, config=connect_config
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

    def _get_raw_connect_config(self) -> Dict[str, Any]:
        try:
            config_result = subprocess.run(
                [self._connect_config_runnable],
                cwd=self._working_path,
                shell=True,
                start_new_session=True,
                check=False,
                capture_output=True,
            )
            if config_result.returncode != 0:
                stdout_str = config_result.stdout.decode("utf-8")
                stderr_str = config_result.stderr.decode("utf-8")
                raise EnvConfigScriptFailed(env_name=self._env_name).add_extra_context(
                    f"stdout: {stdout_str}\nstderr: {stderr_str}"
                )
            config_str = config_result.stdout.decode("utf-8")
            parsed = tomli.loads(config_str)

            # Do some basic validation.
            if "host" not in parsed:
                raise EnvConfigInvalid(env_name=self._env_name).add_extra_context(
                    "Missing 'host' key in connect config."
                )
            if "user" not in parsed:
                raise EnvConfigInvalid(env_name=self._env_name).add_extra_context(
                    "Missing 'user' key in connect config."
                )

            return parsed

        except OSError as ex:
            raise EnvConfigScriptFailed(env_name=self._env_name).add_extra_context(
                str(ex)
            ) from ex
        except tomli.TOMLDecodeError as ex:
            raise EnvConfigInvalid(env_name=self._env_name).add_extra_context(
                str(ex)
            ) from ex
