import time
import webbrowser
import threading
from conductor.errors import MissingExplorerSupport


def start_explorer(host: str, port: int, launch_browser: bool) -> None:
    """
    Entrypoint to launching Conductor's explorer. This function will attempt to
    start the explorer. If the user has not installed the necessary
    dependencies, it will raise an error.
    """

    # We intentionally import this here to gracefully handle cases where the
    # user has not installed Conductor's UI dependencies.
    try:
        import uvicorn
    except ImportError as ex:
        raise MissingExplorerSupport() from ex

    uvicorn_config = uvicorn.Config(
        "conductor.explorer.routes:app",
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(uvicorn_config)

    # Start the server and launch the browser if requested.
    try:
        if launch_browser:
            launch_thread = threading.Thread(
                target=_launch_browser, args=(host, port, 1)
            )
            launch_thread.start()
        else:
            launch_thread = None

        server.run()
    finally:
        if launch_thread is not None:
            launch_thread.join()


def _launch_browser(host: str, port: int, wait_s: int) -> None:
    """
    Launches the user's default browser to the Conductor explorer's URL.
    """
    # We want to start the web browser after the server has started.
    # Unfortunately, uvicorn does not provide any nice "callback"-like
    # mechanisms to know when it has started. So we use this heuristic approach
    # of waiting for a few seconds. This is ugly, but keeps things simple
    # without overengineering something meant to be cosmetic.
    time.sleep(wait_s)
    webbrowser.open(f"http://{host}:{port}")
