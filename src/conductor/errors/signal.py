import signal
from . import ConductorAbort


def register_signal_handlers():
    signal.signal(signal.SIGINT, _terminate_handler)
    signal.signal(signal.SIGTERM, _terminate_handler)


def _terminate_handler(sig, frame):
    raise ConductorAbort()
