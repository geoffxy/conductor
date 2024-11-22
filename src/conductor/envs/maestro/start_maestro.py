import argparse
import asyncio
import grpc
import logging
import pathlib
import conductor.envs.proto_gen.maestro_pb2_grpc as maestro_grpc

from conductor.envs.maestro.daemon import Maestro
from conductor.envs.maestro.grpc import MaestroGrpc
from conductor.utils.logging import set_up_logging
from conductor.config import MAESTRO_ROOT, MAESTRO_LOG_FILE, MAESTRO_PORT

logger = logging.getLogger(__name__)


async def start_maestro(maestro: Maestro, interface: str, port: int) -> None:
    try:
        grpc_server = grpc.aio.server()
        maestro_grpc.add_MaestroServicer_to_server(MaestroGrpc(maestro), grpc_server)
        grpc_server.add_insecure_port(f"{interface}:{port}")
        await grpc_server.start()
        logger.info("The Conductor Maestro daemon has successfully started.")
        logger.info("Listening on port %d.", port)

        # N.B. If we need the Monitor, we should call `run_forever()` here.
        await grpc_server.wait_for_termination()
    finally:
        # Not ideal, but we need to manually call this method to ensure
        # gRPC's internal shutdown process completes before we return from
        # this method.
        grpc_server.__del__()
        logger.debug("Conductor Maestro teardown complete.")


def main():
    """
    This is the main entry point for the Conductor Maestro daemon.
    """
    parser = argparse.ArgumentParser(description="Start the Conductor Maestro daemon.")
    parser.add_argument(
        "--root", type=str, help="The root directory for the Maestro daemon."
    )
    parser.add_argument(
        "--interface", type=str, default="localhost", help="The interface to bind to."
    )
    parser.add_argument(
        "--port", type=int, default=MAESTRO_PORT, help="The port to listen on."
    )
    args = parser.parse_args()

    maestro = Maestro(maestro_root=args.root)
    asyncio.run(start_maestro(maestro, args.interface, args.port))


if __name__ == "__main__":
    home = pathlib.Path.home()
    log_file = home / MAESTRO_ROOT / MAESTRO_LOG_FILE
    set_up_logging(filename=str(log_file))
    main()
