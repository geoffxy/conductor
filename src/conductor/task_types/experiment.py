from conductor.task_types.base import BaseTaskType
from conductor.task_identifier import TaskIdentifier
from conductor.errors import InvalidTaskArguments
from conductor.parsing.validation import generate_type_validator

_TYPE_NAME = "run_experiment"
_SCHEMA = {
    "name": str,
    "exe": str,
}


class RunExperiment(BaseTaskType):
    TypeName = _TYPE_NAME
    _validate = generate_type_validator(_TYPE_NAME, _SCHEMA)

    def __init__(self, name, exe):
        super().__init__(name=name)
        self.exe = exe

    @classmethod
    def from_cond_file(cls, **kwargs):
        cls._validate(kwargs)
        if not TaskIdentifier.is_name_valid(kwargs["name"]):
            raise InvalidTaskArguments(
                "Invalid target identifier '{}'.".format(kwargs["name"]),
            )
        return cls(**kwargs)
