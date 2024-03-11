from threading import Event
from fabric.connection import Connection
from fabric.tunnels import TunnelManager
from invoke.exceptions import ThreadException


class TunneledSshConnection:
    """
    Wraps `fabric.connection.Connection.forward_local()`'s behavior in a class
    since we need more fine-grained control over when a tunnel is created and
    closed.

    This class mimics the behavior of `ssh -L <port>:localhost:<port> <host>`.
    """

    def __init__(self, connection: Connection, port: int) -> None:
        self._port = port
        self._connection = connection
        self._finished = Event()
        self._mgr = TunnelManager(
            "localhost",
            port,
            "localhost",
            port,
            self._connection.transport,
            self._finished,
        )
        self._closed = False

    def port(self) -> int:
        return self._port

    def open(self) -> None:
        self._mgr.start()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._finished.set()
        self._mgr.join()

        # Ensure exceptions are not swallowed.
        wrapper = self._mgr.exception()
        if wrapper is not None:
            if wrapper.type is ThreadException:
                raise wrapper.value
            else:
                raise ThreadException([wrapper])
