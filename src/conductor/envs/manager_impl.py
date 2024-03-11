import time
from fabric import Connection
from conductor.envs.tunneled_ssh_connection import TunneledSshConnection


class EnvManagerImpl:
    def run_test(self, host: str, user: str) -> None:
        c = Connection(host=host, user=user)
        c.open()
        tunnel = TunneledSshConnection(c, port=7023)
        tunnel.open()
        print("Tunnel opened.")
        time.sleep(3)
        tunnel.close()
        print("Tunnel closed.")
        c.close()
        print("Connection closed.")
