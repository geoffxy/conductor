from conductor.envs.maestro.interface import MaestroInterface


class Maestro(MaestroInterface):
    """
    Maestro is Conductor's remote daemon. It runs within a user-defined
    environment and executes tasks when requested by the main Conductor process.
    """

    def __init__(self, maestro_root: str) -> None:
        self._maestro_root = maestro_root

    async def ping(self, message: str) -> str:
        return ""

    async def shutdown(self, key: str) -> str:
        return ""

    def start(self) -> None:
        """
        Start the daemon.
        """
        with open(f"{self._maestro_root}/maestro.log", "w") as log:
            log.write("Hello, Maestro!")
