import pathlib
import time
import io
from typing import Any, Optional

from fabric import Connection

from conductor.envs.tunneled_ssh_connection import TunneledSshConnection
from conductor.envs.install_maestro import ensure_maestro_installed
from conductor.config import MAESTRO_ROOT, MAESTRO_VENV_NAME
from conductor.envs.maestro.client import MaestroGrpcClient


class RemoteEnv:
    """
    Represents a remote environment that has a Maestro daemon running. We
    communicate with the daemon via gRPC over an SSH tunnel.
    """

    @classmethod
    def start(cls, host: str, user: str) -> "RemoteEnv":
        """
        Starts a remote environment on `user@host`. This method is blocking and
        will return after the environment has been started.
        """
        # Open the SSH connection and set up the tunnel.
        conn = Connection(host=host, user=user)
        conn.open()
        # NOTE: Need to cycle through ports until we find one that is open.
        port = 7583
        tunnel = TunneledSshConnection(conn, port=port)
        tunnel.open()

        maestro_root = cls._compute_maestro_root(conn)
        ensure_maestro_installed(conn, maestro_root)

        # Start the daemon in the remote environment.
        venv_python = maestro_root / MAESTRO_VENV_NAME / "bin" / "python3"
        out_pipe = io.StringIO()
        daemon = conn.run(
            f"{str(venv_python)} -m conductor.envs.maestro.start_maestro "
            f"--root {str(maestro_root)} --port {port} --debug",
            asynchronous=True,
            out_stream=out_pipe,
        )
        # The daemon will write a null byte to stdout when it is ready to accept
        # connections. Unfortunately there isn't a nice blocking version of this
        # read API.
        while True:
            if out_pipe.getvalue() != "":
                break
            time.sleep(0.1)
        return cls(
            host="localhost",
            port=port,
            out_pipe=out_pipe,
            connection=conn,
            tunnel=tunnel,
            daemon=daemon,
            maestro_root=maestro_root,
        )

    def __init__(
        self,
        *,
        host: str,
        port: int,
        out_pipe: io.StringIO,
        connection: Connection,
        tunnel: TunneledSshConnection,
        daemon: Any,
        maestro_root: pathlib.Path,
    ) -> None:
        self._host = host
        self._port = port
        self._out_pipe = out_pipe
        self._connection = connection
        self._tunnel = tunnel
        self._daemon = daemon
        self._maestro_root = maestro_root
        self._client: Optional[MaestroGrpcClient] = None

    def client(self) -> MaestroGrpcClient:
        """
        Returns a gRPC client that can be used to communicate with the Maestro
        daemon running in the remote environment.
        """
        if self._client is None:
            self._client = MaestroGrpcClient("localhost", self._port)
            self._client.connect()
        return self._client

    def transfer_file(
        self, local_path: pathlib.Path, remote_path: pathlib.Path
    ) -> None:
        """
        Transfers a file from the local machine to the remote environment. The
        remote path should be a relative path. This method will place the file
        under the Maestro root.
        """
        # Make sure the path (including parent directories) exists.
        full_remote_path = self._maestro_root / remote_path
        self._connection.run(f"mkdir -p {str(full_remote_path.parent)}", hide=True)
        self._connection.put(str(local_path), str(full_remote_path))

    def shutdown(self) -> None:
        """
        Shuts down the remote environment. This terminates the Maestro daemon
        and closes the SSH tunnel. This method is blocking and will return after
        the environment has been shut down.
        """
        client = self.client()
        client.shutdown("shutdown")
        client.close()
        self._client = None
        self._daemon.join()
        self._tunnel.close()
        self._connection.close()
        # N.B. This has to be closed after all the Fabric resources are closed.
        self._out_pipe.close()

    @staticmethod
    def _compute_maestro_root(c: Connection) -> pathlib.Path:
        result = c.run("echo $HOME", hide=True)
        home_dir = result.stdout.strip()
        return pathlib.Path(home_dir) / MAESTRO_ROOT
