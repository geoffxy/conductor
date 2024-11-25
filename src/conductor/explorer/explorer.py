from conductor.errors import MissingExplorerSupport


def start_explorer(host: str, port: int) -> None:
    """
    Entrypoint to launching Conductor's explorer. This function will attempt to
    start the explorer. If the user has not installed the necessary
    dependencies, it will raise an error.
    """

    # We intentionally import this here to gracefully handle cases where the
    # user has not installed Conductor's UI dependencies.
    try:
        import uvicorn

        uvicorn_config = uvicorn.Config(
            "conductor.explorer.routes:app",
            host=host,
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(uvicorn_config)
        server.run()
    except ImportError as ex:
        raise MissingExplorerSupport() from ex
