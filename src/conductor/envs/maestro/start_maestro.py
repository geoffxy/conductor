import argparse
import asyncio
import grpc
import logging
import pathlib
import signal
import conductor.envs.proto_gen.maestro_pb2_grpc as maestro_grpc

from conductor.envs.maestro.daemon import Maestro
from conductor.envs.maestro.grpc_service import MaestroGrpc
from conductor.utils.logging import set_up_logging
from conductor.config import MAESTRO_ROOT, MAESTRO_LOG_FILE

logger = logging.getLogger(__name__)


async def start_maestro(maestro: Maestro, interface: str, port: int) -> None:
    try:
        grpc_server = grpc.aio.server()
        maestro_grpc.add_MaestroServicer_to_server(MaestroGrpc(maestro), grpc_server)
        grpc_server.add_insecure_port(f"{interface}:{port}")
        await grpc_server.start()
        logger.info("The Conductor Maestro daemon has successfully started.")
        logger.info("Listening on port %d.", port)
        await grpc_server.wait_for_termination()
    finally:
        # Not ideal, but we need to manually call this method to ensure
        # gRPC's internal shutdown process completes before we return from
        # this method.
        grpc_server.__del__()
        logger.debug("Conductor Maestro teardown complete.")


async def shutdown_daemon():
    logger.debug("Shutting down the event loop...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def handle_exception(event_loop, context):
    message = context.get("exception", context["message"])
    logger.error("Encountered exception: %s", message)
    logger.error("%s", context)


async def wait_for_all_tasks():
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    await asyncio.gather(*tasks, return_exceptions=True)


def main():
    """
    This is the main entry point for the Conductor Maestro daemon.
    """
    parser = argparse.ArgumentParser(description="Start the Conductor Maestro daemon.")
    parser.add_argument(
        "--root",
        type=str,
        required=True,
        help="The root directory for the Maestro daemon.",
    )
    parser.add_argument(
        "--interface", type=str, default="localhost", help="The interface to bind to."
    )
    parser.add_argument(
        "--port", type=int, required=True, help="The port to listen on."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Set to enable debug logging."
    )
    args = parser.parse_args()

    event_loop = asyncio.new_event_loop()
    event_loop.set_debug(enabled=args.debug)
    asyncio.set_event_loop(event_loop)

    for sig in [signal.SIGTERM, signal.SIGINT]:
        event_loop.add_signal_handler(
            sig, lambda: asyncio.create_task(shutdown_daemon())
        )
    event_loop.set_exception_handler(handle_exception)

    try:
        maestro_root = pathlib.Path(args.root)
        logger.info("Using Maestro root directory: %s", str(maestro_root))
        logger.info("Starting Maestro daemon on %s:%d...", args.interface, args.port)
        maestro = Maestro(maestro_root)
        task = event_loop.create_task(start_maestro(maestro, args.interface, args.port))
        event_loop.run_until_complete(task)
    except asyncio.CancelledError:
        logger.info("Maestro daemon is shutting down...")
    finally:
        wait_task = event_loop.create_task(wait_for_all_tasks())
        event_loop.run_until_complete(wait_task)
        event_loop.stop()
        event_loop.close()
        logger.info("Maestro daemon has shut down successfully.")


if __name__ == "__main__":
    home = pathlib.Path.home()
    log_file = home / MAESTRO_ROOT / MAESTRO_LOG_FILE
    set_up_logging(filename=str(log_file))
    main()
