from typing import Optional
from conductor.utils.output_handler import OutputHandler


class OperationExecutionHandle:
    """
    Represents a possibly asynchronously executing operation.
    """

    def __init__(
        self,
        pid: Optional[int],
    ):
        self.pid: Optional[int] = pid
        self.stdout: Optional[OutputHandler] = None
        self.stderr: Optional[OutputHandler] = None
        self.returncode: Optional[int] = None
        self.slot: Optional[int] = None

    @classmethod
    def from_async_process(cls, pid: int):
        return cls(pid)

    @classmethod
    def from_sync_execution(cls):
        return cls(pid=None)

    @property
    def is_sync(self) -> bool:
        return self.pid is None
