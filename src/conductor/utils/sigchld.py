import contextlib
import errno
import os
import signal
from typing import List, Optional, Tuple  # pylint: disable=unused-import


class SigchldHelper:
    _Instance: "Optional[SigchldHelper]" = None

    @staticmethod
    def instance() -> "SigchldHelper":
        if SigchldHelper._Instance is None:
            SigchldHelper._Instance = SigchldHelper()
        return SigchldHelper._Instance

    def __init__(self):
        # Maps pids to return codes
        self._returncodes: List[Tuple[int, int]] = []
        self._read_pipe = None
        self._write_pipe = None

    @contextlib.contextmanager
    def track(self):
        self._read_pipe, self._write_pipe = os.pipe()
        existing_handler = signal.signal(signal.SIGCHLD, SigchldHelper._handler)
        try:
            yield
        finally:
            signal.signal(signal.SIGCHLD, existing_handler)
            os.close(self._write_pipe)
            os.close(self._read_pipe)
            self._returncodes.clear()
            self._write_pipe = None
            self._read_pipe = None

    def wait(self) -> Tuple[int, int]:
        _ = os.read(self._read_pipe, 1)
        return self._extract_any()

    def _add_returncode(self, pid: int, returncode: int) -> None:
        self._returncodes.append((pid, returncode))
        os.write(self._write_pipe, b"\0")

    def _extract_any(self) -> Tuple[int, int]:
        # Precondition: `self._returncodes` must be non-empty.
        return self._returncodes.pop()

    @staticmethod
    def _handler(sig, frame) -> None:  # pylint: disable=unused-argument
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0 and status == 0:
                    break

                if os.WIFEXITED(status):
                    returncode = os.WEXITSTATUS(status)
                elif os.WIFSIGNALED(status):
                    returncode = os.WTERMSIG(status)
                else:
                    raise AssertionError
                # pylint: disable=protected-access
                SigchldHelper.instance()._add_returncode(pid, returncode)
        except OSError as ex:
            if ex.errno != errno.ECHILD:
                raise
