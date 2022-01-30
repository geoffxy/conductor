import pathlib
import json
from typing import List, Union

from conductor.errors import RunArgumentsNonPrimitiveValue
from conductor.task_identifier import TaskIdentifier

ArgumentValue = Union[str, bool, int, float]


class RunArguments:
    """
    Represents positional arguments that should be passed to a
    `run_experiment()` or `run_command()` task.
    """

    def __init__(self, args: List[ArgumentValue]):
        self._args = args

    @classmethod
    def from_raw(cls, identifier: TaskIdentifier, raw_args: list) -> "RunArguments":
        for arg in raw_args:
            if (
                not isinstance(arg, str)
                and not isinstance(arg, bool)
                and not isinstance(arg, int)
                and not isinstance(arg, float)
            ):
                raise RunArgumentsNonPrimitiveValue(identifier=identifier)
        return cls(raw_args)

    def empty(self) -> bool:
        return len(self._args) == 0

    def serialize_cmdline(self) -> str:
        """
        Serializes the options into a form that can be passed to an
        executable as if it were a command line program.
        """
        args = []
        for arg in self._args:
            if isinstance(arg, bool):
                args.append("true" if arg else "false")
            else:
                args.append(str(arg))
        return " ".join(args)

    def serialize_json(self, file_path: pathlib.Path) -> None:
        """
        Serializes the options into JSON and writes the result to a file at
        `file_path`.
        """
        with open(file_path, "w", encoding="UTF-8") as file:
            json.dump(self._args, file, indent=2)
