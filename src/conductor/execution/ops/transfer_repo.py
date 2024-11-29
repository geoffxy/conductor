import pathlib
from typing import Optional

from conductor.context import Context
from conductor.errors import MissingEnvSupport, EnvsRequireGit
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.ops.operation import Operation
from conductor.execution.operation_state import OperationState
from conductor.config import MAESTRO_BUNDLE_LOCATION


class TransferRepo(Operation):
    """
    Transfers the current repository to a given remote environment.
    """

    def __init__(self, initial_state: OperationState, env_name: str) -> None:
        super().__init__(initial_state)
        self._env_name = env_name

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        if ctx.envs is None:
            raise MissingEnvSupport()
        if not ctx.git.is_used():
            raise EnvsRequireGit()

        # Create a bundle of the current repository.
        repo_name = ctx.project_root.name
        bundle_name = f"{repo_name}.bundle"
        local_bundle_path = ctx.output_path / bundle_name
        ctx.git.create_bundle(symbol="HEAD", bundle_path=local_bundle_path)

        # Transfer the bundle to the remote environment.
        remote_env = ctx.envs.get_remote_env(self._env_name)
        remote_bundle_path = pathlib.Path(MAESTRO_BUNDLE_LOCATION) / bundle_name
        remote_env.transfer_file(local_bundle_path, remote_bundle_path)

        # Remove the local copy.
        local_bundle_path.unlink(missing_ok=True)

        # Unpack the bundle in the remote environment.
        client = remote_env.client()
        workspace_name = client.unpack_bundle(remote_bundle_path)
        remote_env.set_workspace_name(workspace_name)

        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass
