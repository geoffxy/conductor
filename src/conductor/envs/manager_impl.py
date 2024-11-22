from fabric import Connection
from conductor.envs.tunneled_ssh_connection import TunneledSshConnection
from conductor.envs.install_maestro import install_maestro
from conductor.config import MAESTRO_ROOT, MAESTRO_VENV_NAME, MAESTRO_PORT


class EnvManagerImpl:
    def run_test(self, host: str, user: str) -> None:
        c = Connection(host=host, user=user)
        c.open()
        tunnel = TunneledSshConnection(c, port=MAESTRO_PORT)
        tunnel.open()
        print("Tunnel opened.")
        maestro_root = self._compute_maestro_root(c)
        install_maestro(c, maestro_root)
        print("Test launching daemon.")
        # TODO: This needs to be placed in the background or launched on a
        # separate thread (for blocking purposes).
        c.run(
            f"{maestro_root}/{MAESTRO_VENV_NAME}/bin/python3 -m conductor.envs.maestro.run_maestro --root {maestro_root}"
        )
        tunnel.close()
        print("Tunnel closed.")
        c.close()
        print("Connection closed.")

    def _compute_maestro_root(self, c: Connection) -> str:
        result = c.run("echo $HOME")
        home_dir = result.stdout.strip()
        return f"{home_dir}/{MAESTRO_ROOT}"
