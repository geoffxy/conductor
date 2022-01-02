import enum
import pathlib
import subprocess
from concurrent.futures import Future
from typing import Optional, TextIO, IO

import conductor.context as c  # pylint: disable=unused-import


class RecordType(enum.Enum):
    NotRecorded = 1
    Teed = 2
    OnlyLogged = 3


class OutputHandler:
    """
    A utility class used for handling task output logging.
    """

    def __init__(self, output_path: pathlib.Path, record_type: RecordType):
        self._output_path = output_path
        self._type = record_type
        self._file = None
        self._tee_future: Optional[Future] = None

    def popen_arg(self):
        if self._type == RecordType.NotRecorded:
            return None
        elif self._type == RecordType.Teed:
            return subprocess.PIPE
        elif self._type == RecordType.OnlyLogged:
            if self._file is None:
                self._file = open(self._output_path, "wb")
            return self._file

    def maybe_tee(self, pipe: Optional[IO[bytes]], stream: TextIO, ctx: "c.Context"):
        if self._type != RecordType.Teed:
            return
        assert pipe is not None
        self._tee_future = ctx.tee_processor.tee_pipe(pipe, stream, self._output_path)

    def finish(self):
        if self._type == RecordType.Teed and self._tee_future is not None:
            self._tee_future.result()
            self._tee_future = None
        elif self._type == RecordType.OnlyLogged and self._file is not None:
            self._file.close()
            self._file = None

    def __del__(self):
        self.finish()
