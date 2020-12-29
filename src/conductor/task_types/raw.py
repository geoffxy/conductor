from typing import Dict, Type

from conductor.parsing.validation import generate_type_validator
from conductor.task_identifier import TaskIdentifier
from conductor.errors import InvalidTaskName
from .base import TaskType


class RawTaskType:
    def __init__(
        self, name: str, schema: Dict, defaults: Dict, full_type: Type[TaskType]
    ):
        self._name = name
        self._schema = schema
        self._defaults = defaults
        self._full_type = full_type
        self._validator = generate_type_validator(name, schema)

    def __repr__(self) -> str:
        return "".join([self._name, "(", ", ".join(self._schema.keys()), ")"])

    @property
    def name(self) -> str:
        return self._name

    def load_from_cond_file(self, **kwargs) -> Dict:
        args = {**self._defaults, **kwargs}
        self._validator(args)
        if not TaskIdentifier.is_name_valid(args["name"]):
            raise InvalidTaskName(task_name=args["name"])
        return {**args, "_full_type": self._full_type}
