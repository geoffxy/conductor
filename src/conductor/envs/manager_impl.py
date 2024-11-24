from typing import Dict

from conductor.envs.maestro.client import MaestroGrpcClient
from conductor.envs.remote_env import RemoteEnv


class EnvManagerImpl:
    def __init__(self) -> None:
        self._active_envs: Dict[str, RemoteEnv] = {}

    def start_remote_env(self, name: str, host: str, user: str) -> MaestroGrpcClient:
        if name in self._active_envs:
            # This is a internal error as we should not be trying to start an
            # environment more than once.
            raise ValueError(f"Environment with name {name} already exists.")
        remote_env = RemoteEnv.start(host, user)
        self._active_envs[name] = remote_env
        return remote_env.client()

    def get_client(self, name: str) -> MaestroGrpcClient:
        return self._active_envs[name].client()

    def shutdown_remote_env(self, name: str) -> None:
        try:
            self._active_envs[name].shutdown()
            del self._active_envs[name]
        except KeyError as ex:
            # This is a internal error as we should not be trying to stop an
            # environment that does not exist.
            raise ValueError(f"Environment with name {name} does not exist.") from ex
