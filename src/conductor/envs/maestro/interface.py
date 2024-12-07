import pathlib


class MaestroInterface:
    """
    Captures the RPC interface for Maestro. We use this interface to separate
    the gRPC implementation details from Maestro.
    """

    async def ping(self, message: str) -> str:
        raise NotImplementedError

    async def unpack_bundle(self, bundle_path: pathlib.Path) -> str:
        raise NotImplementedError

    async def shutdown(self, key: str) -> str:
        raise NotImplementedError
