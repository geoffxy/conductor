from conductor.target_name import TargetName
from conductor.errors import InvalidRuleArguments
from .validation import generate_type_validator

_schema = {
    "name": str,
    "exe": str,
}


class RunExperiment:
    validate = generate_type_validator("run_experiment", _schema)

    def __init__(self, name, exe):
        self.name = name
        self.exe = exe

    @classmethod
    def rule(cls, **kwargs):
        cls.validate(kwargs)
        if not TargetName.is_identifier_valid(kwargs["name"]):
            raise InvalidRuleArguments(
                "Invalid target identifier '{}'.".format(kwargs["name"]),
            )
        return cls(**kwargs)
