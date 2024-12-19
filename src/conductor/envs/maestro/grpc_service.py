import pathlib
import conductor.envs.proto_gen.maestro_pb2_grpc as rpc
import conductor.envs.proto_gen.maestro_pb2 as pb
from conductor.envs.maestro.interface import MaestroInterface
from conductor.errors import ConductorError
from conductor.task_identifier import TaskIdentifier

# pylint: disable=no-member
# See https://github.com/protocolbuffers/protobuf/issues/10372

# pylint: disable=invalid-overridden-method


class MaestroGrpc(rpc.MaestroServicer):
    """
    A shim layer used to implement Maestro's gRPC interface.
    """

    def __init__(self, maestro: MaestroInterface) -> None:
        self._maestro = maestro

    async def UnpackBundle(
        self, request: pb.UnpackBundleRequest, context
    ) -> pb.UnpackBundleResult:
        try:
            bundle_path = pathlib.Path(request.bundle_path)
            workspace_name = await self._maestro.unpack_bundle(bundle_path)
            return pb.UnpackBundleResult(
                response=pb.UnpackBundleResponse(workspace_name=workspace_name)
            )
        except ConductorError as ex:
            return pb.UnpackBundleResult(error=_error_to_pb(ex))

    async def ExecuteTask(
        self, request: pb.ExecuteTaskRequest, context
    ) -> pb.ExecuteTaskResult:
        try:
            workspace_name = request.workspace_name
            project_root = pathlib.Path(request.project_root)
            task_identifier = TaskIdentifier.from_str(request.task_identifier)
            await self._maestro.execute_task(
                workspace_name, project_root, task_identifier
            )
            return pb.ExecuteTaskResult(response=pb.ExecuteTaskResponse())
        except ConductorError as ex:
            return pb.ExecuteTaskResult(error=_error_to_pb(ex))

    async def Shutdown(self, request: pb.ShutdownRequest, context) -> pb.ShutdownResult:
        try:
            response_message = await self._maestro.shutdown(request.key)
            return pb.ShutdownResult(
                response=pb.ShutdownResponse(message=response_message)
            )
        except ConductorError as ex:
            return pb.ShutdownResult(error=_error_to_pb(ex))


def _error_to_pb(ex: ConductorError) -> pb.ConductorError:
    error = pb.ConductorError()
    error.code = ex.error_code
    for kwarg, kwarg_val in ex.kwargs.items():
        msg = error.kwargs.add()
        msg.key = str(kwarg)
        msg.value = str(kwarg_val)

    file_context = ex.file_context
    if file_context is not None:
        error.file_context_path = file_context.file_path
        error.file_context_line_number = file_context.line_number

    if ex.extra_context is not None:
        error.extra_context = ex.extra_context

    return error
