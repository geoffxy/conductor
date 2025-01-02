from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from conductor.envs.remote_env import RemoteEnv


class EnvManager:
    """
    Manages Conductor's active environments.
    """

    @classmethod
    def create(cls) -> Optional["EnvManager"]:
        """
        Create a new instance of the environment manager. This will return
        `None` if environments are unsupported (which happens if the user has
        not installed the required dependencies.)
        """
        try:
            import conductor.envs.manager_impl as mgr_impl

            return cls(mgr_impl.EnvManagerImpl())

        except ImportError:
            # Environments are unsupported. The user did not install the
            # required dependencies.
            return None

    def __init__(self, impl: Any) -> None:
        # We use a separate Impl class to gracefully support versions of
        # Conductor without environment support (to mimimize the number of
        # dependencies we need).
        import conductor.envs.manager_impl as mgr_impl

        self._impl: mgr_impl.EnvManagerImpl = impl

    def start_remote_env(
        self, name: str, host: str, user: str, config: Dict[str, Any]
    ) -> "RemoteEnv":
        return self._impl.start_remote_env(name, host, user, config)

    def get_remote_env(self, name: str) -> "RemoteEnv":
        return self._impl.get_remote_env(name)

    def shutdown_remote_env(self, name: str) -> None:
        return self._impl.shutdown_remote_env(name)
