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
                # Read up to 4096 bytes at a time, but return as soon as we read
                # some bytes.
                data = pipe.read1(4096)  # type: ignore
                if len(data) == 0:
                    # End of the stream.
                    break
                file.write(data)
                stream.buffer.write(data)
                # Needed to maintain interactivity.
                stream.flush()
            stream.flush()
