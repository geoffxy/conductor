from fabric import Connection
from conductor.envs.tunneled_ssh_connection import TunneledSshConnection
from conductor.envs.install_maestro import install_maestro


class EnvManagerImpl:
    def run_test(self, host: str, user: str) -> None:
        c = Connection(host=host, user=user)
        c.open()
        tunnel = TunneledSshConnection(c, port=7023)
        tunnel.open()
        print("Tunnel opened.")
        install_maestro(c)
        tunnel.close()
        print("Tunnel closed.")
        c.close()
        print("Connection closed.")
