from typing import Optional

from conductor.context import Context
from conductor.errors import MissingEnvSupport
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.operation_state import OperationState
from conductor.execution.ops.operation import Operation


class StartRemoteEnv(Operation):
    def __init__(
        self, initial_state: OperationState, env_name: str, start_runnable: str
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._start_runnable = start_runnable

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        if ctx.envs is None:
            raise MissingEnvSupport()

        # - Execute the runnable
        # - Open a new SSH connection and tunnel
        # - Install/start Maestro

        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass
