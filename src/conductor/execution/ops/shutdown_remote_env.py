from typing import Optional

from conductor.context import Context
from conductor.errors import MissingEnvSupport
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.operation_state import OperationState
from conductor.execution.ops.operation import Operation


class ShutdownRemoteEnv(Operation):
    def __init__(
        self, initial_state: OperationState, env_name: str, shutdown_runnable: str
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._shutdown_runnable = shutdown_runnable

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        if ctx.envs is None:
            raise MissingEnvSupport()

        # - Shutdown Maestro
        # - Close SSH connection and tunnel
        # - Execute the runnable

        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass
