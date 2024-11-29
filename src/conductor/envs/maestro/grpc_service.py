import pathlib
import conductor.envs.proto_gen.maestro_pb2_grpc as rpc
import conductor.envs.proto_gen.maestro_pb2 as pb
from conductor.envs.maestro.interface import MaestroInterface

# pylint: disable=no-member
# See https://github.com/protocolbuffers/protobuf/issues/10372

# pylint: disable=invalid-overridden-method


class MaestroGrpc(rpc.MaestroServicer):
    """
    A shim layer used to implement Maestro's gRPC interface.
    """

    def __init__(self, maestro: MaestroInterface) -> None:
        self._maestro = maestro

    async def Ping(self, request: pb.PingRequest, context) -> pb.PingResponse:
        response_message = await self._maestro.ping(request.message)
        return pb.PingResponse(message=response_message)

    async def UnpackBundle(
        self, request: pb.UnpackBundleRequest, context
    ) -> pb.UnpackBundleResponse:
        bundle_path = pathlib.Path(request.bundle_path)
        workspace_name = await self._maestro.unpack_bundle(bundle_path)
        return pb.UnpackBundleResponse(workspace_name=workspace_name)

    async def Shutdown(
        self, request: pb.ShutdownRequest, context
    ) -> pb.ShutdownResponse:
        response_message = await self._maestro.shutdown(request.key)
        return pb.ShutdownResponse(message=response_message)
