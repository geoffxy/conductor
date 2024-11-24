import time
from fabric import Connection
from conductor.envs.tunneled_ssh_connection import TunneledSshConnection
from conductor.envs.install_maestro import install_maestro
from conductor.config import MAESTRO_ROOT, MAESTRO_VENV_NAME
from conductor.envs.maestro.client import MaestroGrpcClient


class EnvManagerImpl:
    def run_test(self, host: str, user: str) -> None:
        c = Connection(host=host, user=user)
        c.open()
        port = 7583
        tunnel = TunneledSshConnection(c, port=port)
        tunnel.open()
        print("Tunnel opened.")
        maestro_root = self._compute_maestro_root(c)
        install_maestro(c, maestro_root)
        print("Test launching daemon.")
        daemon = c.run(
            f"{maestro_root}/{MAESTRO_VENV_NAME}/bin/python3 -m "
            f"conductor.envs.maestro.start_maestro --root {maestro_root} --port {port} --debug",
            asynchronous=True,
        )
        print("Daemon launched.")
        time.sleep(3)
        try:
            with MaestroGrpcClient("localhost", port) as client:
                print("Test pinging daemon.")
                response = client.ping("ping")
                print("Ping response:", response)
                print("Sending shutdown")
                response = client.shutdown("shutdown")
                print("Shutdown response:", response)
            daemon.join()
        finally:
            tunnel.close()
            print("Tunnel closed.")
            c.close()
            print("Connection closed.")

    def _compute_maestro_root(self, c: Connection) -> str:
        result = c.run("echo $HOME")
        home_dir = result.stdout.strip()
        return f"{home_dir}/{MAESTRO_ROOT}"
