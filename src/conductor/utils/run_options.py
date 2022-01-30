import pathlib
import json
from typing import Dict, Union

from conductor.config import EXP_OPTION_CMD_FORMAT
from conductor.errors import (
    RunOptionsNonPrimitiveValue,
    RunOptionsNonStringKey,
)
from conductor.task_identifier import TaskIdentifier

OptionValue = Union[str, bool, int, float]


class RunOptions:
    """
    Represents key-value options that should be passed to a
    `run_experiment()` or `run_command()` task.
    """

    def __init__(self, options: Dict[str, OptionValue]):
        self._options = options

    @classmethod
    def from_raw(cls, identifier: TaskIdentifier, raw_options: dict) -> "RunOptions":
        for key, value in raw_options.items():
            if not isinstance(key, str):
                raise RunOptionsNonStringKey(identifier=identifier)
            if (
                not isinstance(value, str)
                and not isinstance(value, bool)
                and not isinstance(value, int)
                and not isinstance(value, float)
            ):
                raise RunOptionsNonPrimitiveValue(identifier=identifier, key=key)
        return cls(raw_options)

    def empty(self) -> bool:
        return len(self._options) == 0

    def serialize_cmdline(self) -> str:
        """
        Serializes the options into a form that can be passed to an
        executable as if it were a command line program.
        e.g., "--threads=3 --memory=2"
        """
        options = []
        for key, value in self._options.items():
            if isinstance(value, bool):
                options.append(
                    EXP_OPTION_CMD_FORMAT.format(
                        key=key, value="true" if value else "false"
                    )
                )
            else:
                options.append(EXP_OPTION_CMD_FORMAT.format(key=key, value=str(value)))
        return " ".join(options)

    def serialize_json(self, file_path: pathlib.Path) -> None:
        """
        Serializes the options into JSON and writes the result to a file at
        `file_path`.
        """
        with open(file_path, "w", encoding="UTF-8") as file:
            json.dump(self._options, file, indent=2, sort_keys=True)
