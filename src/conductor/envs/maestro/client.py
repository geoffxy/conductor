import grpc
import pathlib
from typing import Dict, Optional, List, Tuple

import conductor.envs.proto_gen.maestro_pb2 as pb
import conductor.envs.proto_gen.maestro_pb2_grpc as maestro_grpc
from conductor.envs.maestro.interface import (
    ExecuteTaskResponse,
    ExecuteTaskType,
    PackTaskOutputsResponse,
)
from conductor.task_identifier import TaskIdentifier
from conductor.errors import ConductorError, InternalError
from conductor.errors.generated import ERRORS_BY_CODE
from conductor.execution.version_index import Version


class MaestroGrpcClient:
    """
    A wrapper over Maestro's gRPC stub, to simplify programmatic access through
    Python.

    This client is a thin wrapper over the gRPC stub. Methods on this client are
    synchronous.

    Usage:
    ```
    with MaestroGrpcClient(host, port) as client:
        # RPC calls here.
        pass
    ```
    """

    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._channel = None
        self._stub: Optional[maestro_grpc.MaestroStub] = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect(self) -> None:
        self._channel = grpc.insecure_channel("{}:{}".format(self._host, self._port))
        self._stub = maestro_grpc.MaestroStub(self._channel)

    def unpack_bundle(self, bundle_path: pathlib.Path) -> str:
        assert self._stub is not None
        # pylint: disable-next=no-member
        msg = pb.UnpackBundleRequest(bundle_path=str(bundle_path))
        result = self._stub.UnpackBundle(msg)
        if result.WhichOneof("result") == "error":
            raise _pb_to_error(result.error)
        return result.response.workspace_name

    def execute_task(
        self,
        workspace_name: str,
        workspace_rel_project_root: pathlib.Path,
        task_identifier: TaskIdentifier,
        dep_versions: Dict[TaskIdentifier, Version],
        execute_task_type: ExecuteTaskType,
    ) -> ExecuteTaskResponse:
        assert self._stub is not None
        # pylint: disable-next=no-member
        msg = pb.ExecuteTaskRequest(
            workspace_name=workspace_name,
            project_root=str(workspace_rel_project_root),
            task_identifier=str(task_identifier),
        )
        for task_id, version in dep_versions.items():
            dv = msg.dep_versions.add()
            dv.task_identifier = str(task_id)
            dv.version.timestamp = version.timestamp
            if version.commit_hash is not None:
                dv.version.commit_hash = version.commit_hash
            dv.version.has_uncommitted_changes = version.has_uncommitted_changes
        if execute_task_type == ExecuteTaskType.RunExperiment:
            msg.execute_task_type = pb.TT_RUN_EXPERIMENT  # pylint: disable=no-member
        elif execute_task_type == ExecuteTaskType.RunCommand:
            msg.execute_task_type = pb.TT_RUN_COMMAND  # pylint: disable=no-member
        else:
            raise InternalError(
                details=f"Unsupported execute task type {str(execute_task_type)}."
            )
        result = self._stub.ExecuteTask(msg)
        if result.WhichOneof("result") == "error":
            raise _pb_to_error(result.error)
        response = result.response
        return ExecuteTaskResponse(
            start_timestamp=response.start_timestamp,
            end_timestamp=response.end_timestamp,
            version=(
                None
                if response.version.timestamp == 0
                else Version(
                    timestamp=response.version.timestamp,
                    commit_hash=response.version.commit_hash,
                    has_uncommitted_changes=response.version.has_uncommitted_changes,
                )
            ),
        )

    def unpack_task_outputs(
        self,
        workspace_name: str,
        workspace_rel_project_root: pathlib.Path,
        archive_path: pathlib.Path,
    ) -> int:
        assert self._stub is not None
        # pylint: disable-next=no-member
        msg = pb.UnpackTaskOutputsRequest(
            workspace_name=workspace_name,
            project_root=str(workspace_rel_project_root),
            task_archive_path=str(archive_path),
        )
        result = self._stub.UnpackTaskOutputs(msg)
        if result.WhichOneof("result") == "error":
            raise _pb_to_error(result.error)
        return result.response.num_unpacked_tasks

    def pack_task_outputs(
        self,
        workspace_name: str,
        workspace_rel_project_root: pathlib.Path,
        versioned_tasks: List[Tuple[TaskIdentifier, Version]],
        unversioned_tasks: List[TaskIdentifier],
    ) -> PackTaskOutputsResponse:
        assert self._stub is not None
        # pylint: disable-next=no-member
        msg = pb.PackTaskOutputsRequest(
            workspace_name=workspace_name,
            project_root=str(workspace_rel_project_root),
        )
        for task_id, version in versioned_tasks:
            vt = msg.versioned_tasks.add()
            vt.task_identifier = str(task_id)
            vt.version.timestamp = version.timestamp
            if version.commit_hash is not None:
                vt.version.commit_hash = version.commit_hash
            vt.version.has_uncommitted_changes = version.has_uncommitted_changes
        for task_id in unversioned_tasks:
            msg.unversioned_task_identifiers.append(str(task_id))
        result = self._stub.PackTaskOutputs(msg)
        if result.WhichOneof("result") == "error":
            raise _pb_to_error(result.error)
        response = result.response
        return PackTaskOutputsResponse(
            num_packed_tasks=response.num_packed_tasks,
            task_archive_path=pathlib.Path(response.task_archive_path),
        )

    def shutdown(self, key: str) -> str:
        assert self._stub is not None
        # pylint: disable-next=no-member
        msg = pb.ShutdownRequest(key=key)
        result = self._stub.Shutdown(msg)
        if result.WhichOneof("result") == "error":
            raise _pb_to_error(result.error)
        return result.response.message

    def close(self) -> None:
        assert self._stub is not None
        assert self._channel is not None
        self._stub = None
        self._channel.close()
        self._channel = None


# pylint: disable-next=no-member
def _pb_to_error(ex: pb.ConductorError) -> ConductorError:
    exception_class = ERRORS_BY_CODE[ex.code]
    kwargs = {}
    for kwarg in ex.kwargs:
        kwargs[kwarg.key] = kwarg.value
    error: ConductorError = exception_class(**kwargs)
    if ex.file_context_path is not None:
        error.add_file_context(ex.file_context_path, ex.file_context_line_number)
    if ex.extra_context is not None:
        error.add_extra_context(ex.extra_context)
    return error
