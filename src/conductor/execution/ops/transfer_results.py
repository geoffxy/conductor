import enum
import pathlib
from typing import Optional, List, Tuple

from conductor.context import Context
from conductor.errors import MissingEnvSupport, EnvsRequireGit, InternalError
from conductor.execution.handle import OperationExecutionHandle
from conductor.execution.ops.operation import Operation
from conductor.execution.operation_state import OperationState
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier
from conductor.utils.output_archiving import (
    create_archive,
    restore_archive,
    platform_archive_type,
    generate_archive_name,
)
from conductor.config import MAESTRO_TASK_TRANSFER_LOCATION


class TransferDirection(enum.Enum):
    ToEnv = "to_env"
    FromEnv = "from_env"


class TransferResults(Operation):
    """
    Transfer task results to/from a remote environment.
    """

    def __init__(
        self,
        initial_state: OperationState,
        env_name: str,
        workspace_rel_project_root: pathlib.Path,
        versioned_tasks: List[Tuple[TaskIdentifier, Version]],
        unversioned_tasks: List[TaskIdentifier],
        direction: TransferDirection,
    ) -> None:
        super().__init__(initial_state)
        self._env_name = env_name
        self._project_root = workspace_rel_project_root
        self._versioned_tasks = versioned_tasks
        self._unversioned_tasks = unversioned_tasks
        self._direction = direction

    @property
    def direction(self) -> TransferDirection:
        return self._direction

    @property
    def env_name(self) -> str:
        return self._env_name

    @property
    def versioned_tasks(self) -> List[Tuple[TaskIdentifier, Version]]:
        return self._versioned_tasks

    @property
    def unversioned_tasks(self) -> List[TaskIdentifier]:
        return self._unversioned_tasks

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
        archive_type = platform_archive_type()

        if self._direction == TransferDirection.ToEnv:
            archive_name = generate_archive_name(archive_type)
            out_archive_path = ctx.output_path / archive_name
            tasks_to_archive: List[Tuple[TaskIdentifier, Optional[Version]]] = (
                self._versioned_tasks
                + [(task, None) for task in self._unversioned_tasks]
            )
            try:
                num_archived = create_archive(
                    ctx, tasks_to_archive, out_archive_path, archive_type
                )
                if num_archived != len(tasks_to_archive):
                    raise InternalError(
                        details="Not all tasks were archived. Expected "
                        f"{len(tasks_to_archive)}, got {num_archived}."
                    )
                remote_archive_path = (
                    pathlib.Path(MAESTRO_TASK_TRANSFER_LOCATION)
                    / workspace_name
                    / archive_name
                )
                remote_env.transfer_file(out_archive_path, remote_archive_path)
                num_unpacked = client.unpack_task_outputs(
                    workspace_name,
                    self._project_root,
                    pathlib.Path(archive_name),
                    archive_type,
                )
                if num_unpacked != num_archived:
                    raise InternalError(
                        details="Not all tasks were unpacked in the remote "
                        f"environment. Expected {num_archived}, got "
                        f"{num_unpacked}."
                    )
            finally:
                out_archive_path.unlink(missing_ok=True)
                remote_env.delete_file(remote_archive_path)
        elif self._direction == TransferDirection.FromEnv:
            try:
                result = client.pack_task_outputs(
                    remote_env.workspace_name(),
                    self._project_root,
                    self._versioned_tasks,
                    self._unversioned_tasks,
                    archive_type,
                )
                if result.num_packed_tasks != len(self._versioned_tasks) + len(
                    self._unversioned_tasks
                ):
                    raise InternalError(
                        details="Not all tasks were packed. Expected "
                        f"{len(self._versioned_tasks) + len(self._unversioned_tasks)}, "
                        f"got {result.num_packed_tasks}."
                    )
                remote_archive_path = (
                    pathlib.Path(MAESTRO_TASK_TRANSFER_LOCATION)
                    / workspace_name
                    / result.task_archive_path
                )
                local_archive_path = ctx.output_path / result.task_archive_path
                remote_env.pull_file(remote_archive_path, local_archive_path)
                num_extracted = restore_archive(
                    ctx, local_archive_path, archive_type, expect_no_duplicates=False
                )
                if num_extracted != len(self._versioned_tasks) + len(
                    self._unversioned_tasks
                ):
                    raise InternalError(
                        details="Not all tasks were restored from the archive. "
                        f"Expected {len(self._versioned_tasks) + len(self._unversioned_tasks)}, "
                        f"got {num_extracted}."
                    )
            finally:
                remote_env.delete_file(remote_archive_path)
                local_archive_path.unlink(missing_ok=True)

        else:
            raise InternalError(
                details=f"Unsupported transfer direction: {self._direction}"
            )

        return OperationExecutionHandle.from_sync_execution()

    def finish_execution(self, handle: OperationExecutionHandle, ctx: Context) -> None:
        pass
