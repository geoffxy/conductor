from conductor.parsing.validation import generate_type_validator
from conductor.task_identifier import TaskIdentifier
from conductor.errors import InvalidTaskName


class RawTaskType:
    def __init__(self, name, schema, full_type):
        self._name = name
        self._schema = schema
        self._full_type = full_type
        self._validator = generate_type_validator(name, schema)

    def __repr__(self):
        return "".join([self._name, "(", ", ".join(self._schema.keys()), ")"])

    @property
    def name(self):
        return self._name

    def load_from_cond_file(self, **kwargs):
        self._validator(kwargs)
        if not TaskIdentifier.is_name_valid(kwargs["name"]):
            raise InvalidTaskName(task_name=kwargs["name"])
        return {
            **kwargs,
            "_full_type": self._full_type,
        }
