import collections
import os

FileContext = collections.namedtuple(
    "FileContext",
    ["file_path", "line_number"],
)


class ConductorError(RuntimeError):
    def __init__(self, *args):
        super().__init__(*args)
        self.file_context = None

    def add_file_context(self, file_path, line_number=None):
        self.file_context = FileContext(file_path, line_number)

    def __repr__(self):
        return self.__class__.__name__

    def _message(self):
        raise NotImplementedError

    def printable_message(self):
        if self.file_context is None:
            return self._message()
        elif self.file_context.line_number is None:
            return "".join(
                [
                    self._message(),
                    os.linesep,
                    os.linesep,
                    "-> Relevant file: ",
                    self.file_context.file_path,
                ]
            )
        else:
            return "".join(
                [
                    self._message(),
                    os.linesep,
                    os.linesep,
                    "-> Line ",
                    str(self.file_context.line_number),
                    " in file: ",
                    self.file_context.file_path,
                ]
            )
