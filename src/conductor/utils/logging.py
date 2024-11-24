import logging
from typing import Any, Dict, Optional

VERBOSE = 5


def log_verbose(logger: logging.Logger, message: str, *args) -> None:
    logger.log(VERBOSE, message, *args)


def set_up_logging(
    filename: Optional[str] = None, debug_mode: bool = False, also_console: bool = False
) -> None:
    logging_kwargs: Dict[str, Any] = {
        "format": "%(asctime)s %(levelname)-8s %(message)s",
        "datefmt": "%Y-%m-%d %H:%M",
        "level": logging.DEBUG if debug_mode else logging.INFO,
    }
    if filename is not None and not also_console:
        # Logs will be written to a file.
        logging_kwargs["filename"] = filename
    elif filename is not None and also_console:
        logging_kwargs["handlers"] = [
            logging.FileHandler(filename),
            logging.StreamHandler(),
        ]
    logging.basicConfig(**logging_kwargs)  # type: ignore
    logging.addLevelName(VERBOSE, "VERBOSE")

    # Avoids the "Using selector: EpollSelector" (or similar) messages.
    logging.getLogger("asyncio").setLevel(logging.INFO)
