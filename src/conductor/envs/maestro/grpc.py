import conductor.envs.proto_gen.maestro_pb2_grpc as rpc
import conductor.envs.proto_gen.maestro_pb2 as pb
from conductor.envs.maestro.interface import MaestroInterface


class MaestroGrpc(rpc.MaestroServicer):
    """
    A shim layer used to implement Maestro's gRPC interface.
    """

    def __init__(self, maestro: MaestroInterface) -> None:
        self._maestro = maestro

    async def Ping(self, request: pb.PingRequest, context) -> pb.PingResponse:
        response_message = await self._maestro.ping(request.message)
        return pb.PingResponse(message=response_message)

    async def Shutdown(
        self, request: pb.ShutdownRequest, context
    ) -> pb.ShutdownResponse:
        response_message = await self._maestro.shutdown(request.key)
        return pb.ShutdownResponse(message=response_message)
