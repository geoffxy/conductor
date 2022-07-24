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
        self.extra_context = None

    def add_file_context(self, file_path, line_number=None):
        self.file_context = FileContext(file_path, line_number)
        return self

    def add_file_context_if_missing(self, file_path, line_number=None):
        if self.file_context is not None:
            return self
        return self.add_file_context(file_path, line_number)

    def add_extra_context(self, context_string):
        self.extra_context = context_string
        return self

    def __repr__(self):
        return self.__class__.__name__

    def _message(self):
        raise NotImplementedError

    def printable_message(self, omit_file_context=False):
        full_message = self._message()
        if self.extra_context is not None:
            full_message += " " + self.extra_context

        if self.file_context is None or omit_file_context:
            return full_message
        elif self.file_context.line_number is None:
            return "".join(
                [
                    full_message,
                    os.linesep,
                    os.linesep,
                    "-> Relevant file: ",
                    str(self.file_context.file_path),
                ]
            )
        else:
            return "".join(
                [
                    full_message,
                    os.linesep,
                    os.linesep,
                    "-> Line ",
                    str(self.file_context.line_number),
                    " in file: ",
                    str(self.file_context.file_path),
                ]
            )
