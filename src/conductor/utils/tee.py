import pathlib
from concurrent.futures import ThreadPoolExecutor, Future
from typing import IO, TextIO


class TeeProcessor:
    """
    A utility that uses threads to implement tee-like functionality.
    """

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)

    def __del__(self):
        self._executor.shutdown(wait=True)

    def tee_pipe(
        self, pipe: IO[bytes], stream: TextIO, file_name: pathlib.Path
    ) -> Future:
        return self._executor.submit(self._tee_pipe_run, pipe, stream, file_name)

    def _tee_pipe_run(
        self, pipe: IO[bytes], stream: TextIO, file_name: pathlib.Path
    ) -> None:
        with open(file_name, "wb") as file:
            while True:
                data = pipe.read()
                if len(data) == 0:
                    break
                file.write(data)
                stream.write(data.decode(stream.encoding))
            stream.flush()
