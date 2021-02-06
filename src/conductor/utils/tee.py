import pathlib
from concurrent.futures import ThreadPoolExecutor, Future
from typing import IO, TextIO


class TeeProcessor:
    """
    A utility that uses threads to implement tee-like functionality.
    """

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._has_shutdown = False

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        if self._has_shutdown:
            return
        self._executor.shutdown(wait=True)
        self._has_shutdown = True

    def tee_pipe(
        self, pipe: IO[bytes], stream: TextIO, file_name: pathlib.Path
    ) -> Future:
        return self._executor.submit(self._tee_pipe_run, pipe, stream, file_name)

    def _tee_pipe_run(
        self, pipe: IO[bytes], stream: TextIO, file_name: pathlib.Path
    ) -> None:
        with open(file_name, "wb") as file:
            while True:
                # We want the output to be interactive, so we make sure to
                # immediately write out every byte we receive. However, we
                # still rely on any write buffering used by the file and
                # stream.
                data = pipe.read(1)
                if len(data) == 0:
                    break
                file.write(data)
                stream.write(data.decode(stream.encoding))
            stream.flush()
