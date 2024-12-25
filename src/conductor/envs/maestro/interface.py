import enum
import pathlib
from typing import Dict, NamedTuple, List, Tuple, Optional
from conductor.task_identifier import TaskIdentifier
from conductor.execution.version_index import Version
from conductor.utils.output_archiving import ArchiveType


class ExecuteTaskResponse(NamedTuple):
    start_timestamp: int
    end_timestamp: int
    version: Optional[Version]


class ExecuteTaskType(enum.Enum):
    RunExperiment = "run_experiment"
    RunCommand = "run_command"


class PackTaskOutputsResponse(NamedTuple):
    num_packed_tasks: int
    task_archive_path: pathlib.Path


class MaestroInterface:
    """
    Captures the RPC interface for Maestro. We use this interface to separate
    the gRPC implementation details from Maestro.
    """

    async def unpack_bundle(self, bundle_path: pathlib.Path) -> str:
        raise NotImplementedError

    async def execute_task(
        self,
        workspace_name: str,
        project_root: pathlib.Path,
        task_identifier: TaskIdentifier,
        dep_versions: Dict[TaskIdentifier, Version],
        execute_task_type: ExecuteTaskType,
    ) -> ExecuteTaskResponse:
        raise NotImplementedError

    async def unpack_task_outputs(
        self,
        workspace_name: str,
        project_root: pathlib.Path,
        archive_path: pathlib.Path,
        archive_type: ArchiveType,
    ) -> int:
        raise NotImplementedError

    async def pack_task_outputs(
        self,
        workspace_name: str,
        project_root: pathlib.Path,
        versioned_tasks: List[Tuple[TaskIdentifier, Version]],
        unversioned_tasks: List[TaskIdentifier],
        archive_type: ArchiveType,
    ) -> PackTaskOutputsResponse:
        raise NotImplementedError

    async def shutdown(self, key: str) -> str:
        raise NotImplementedError
