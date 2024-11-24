import grpc
from typing import Optional
import conductor.envs.proto_gen.maestro_pb2 as pb
import conductor.envs.proto_gen.maestro_pb2_grpc as maestro_grpc


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

    def ping(self, message: str) -> str:
        assert self._stub is not None
        # pylint: disable-next=no-member
        msg = pb.PingRequest(message=message)
        return self._stub.Ping(msg).message

    def shutdown(self, key: str) -> str:
        assert self._stub is not None
        # pylint: disable-next=no-member
        msg = pb.ShutdownRequest(key=key)
        return self._stub.Shutdown(msg).message

    def close(self) -> None:
        assert self._stub is not None
        assert self._channel is not None
        self._stub = None
        self._channel.close()
        self._channel = None
