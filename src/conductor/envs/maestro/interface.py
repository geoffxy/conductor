import enum
import pathlib
from typing import Dict, NamedTuple
from conductor.task_identifier import TaskIdentifier
from conductor.execution.version_index import Version


class ExecuteTaskResponse(NamedTuple):
    start_timestamp: int
    end_timestamp: int


class ExecuteTaskType(enum.Enum):
    RunExperiment = "run_experiment"
    RunCommand = "run_command"


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

    async def shutdown(self, key: str) -> str:
        raise NotImplementedError
