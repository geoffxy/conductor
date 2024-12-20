import pathlib
from typing import Dict, Optional

from conductor.context import Context
from conductor.errors import MissingEnvSupport, EnvsRequireGit
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.ops.operation import Operation
from conductor.execution.operation_state import OperationState
from conductor.task_identifier import TaskIdentifier
from conductor.execution.version_index import Version


class RunRemoteTask(Operation):
    """
    Runs a task (given by identifier) in a remote environment.
    """

    def __init__(
        self,
        initial_state: OperationState,
        *,
        env_name: str,
        workspace_rel_project_root: pathlib.Path,
        task_identifier: TaskIdentifier,
        dep_versions: Dict[TaskIdentifier, Version],
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._task_identifier = task_identifier
        self._dep_versions = dep_versions
        self._project_root = workspace_rel_project_root

    def start_execution(
        self, ctx: Context, slot: Optional[int]
    ) -> OperationExecutionHandle:
        if ctx.envs is None:
            raise MissingEnvSupport()
        if not ctx.git.is_used():
            raise EnvsRequireGit()

        remote_env = ctx.envs.get_remote_env(self._env_name)
        client = remote_env.client()
        workspace_name = remote_env.workspace_name()
        # NOTE: This can be made asynchronous if needed.
        client.execute_task(
            workspace_name,
            self._project_root,
            self._task_identifier,
            self._dep_versions,
        )
        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass
