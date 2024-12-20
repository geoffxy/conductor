import grpc
import pathlib
from typing import Dict, Optional

import conductor.envs.proto_gen.maestro_pb2 as pb
import conductor.envs.proto_gen.maestro_pb2_grpc as maestro_grpc
from conductor.envs.maestro.interface import ExecuteTaskResponse
from conductor.task_identifier import TaskIdentifier
from conductor.errors import ConductorError
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
        result = self._stub.ExecuteTask(msg)
        if result.WhichOneof("result") == "error":
            raise _pb_to_error(result.error)
        response = result.response
        return ExecuteTaskResponse(
            start_timestamp=response.start_timestamp,
            end_timestamp=response.end_timestamp,
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
