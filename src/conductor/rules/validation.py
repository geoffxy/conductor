from conductor.errors import InvalidRuleArguments


def generate_type_validator(rule_name, schema):
    def validate(arguments):
        for parameter, type in schema.items():
            if parameter not in arguments:
                raise InvalidRuleArguments(
                    "Missing '{}' argument in {}.".format(
                        parameter,
                        rule_name,
                    ),
                )
            if not isinstance(arguments[parameter], type):
                raise InvalidRuleArguments(
                    "Invalid type for argument '{}' (expected {}).".format(
                        parameter,
                        type.__name__,
                    ),
                )
        if len(arguments) != len(schema):
            raise InvalidRuleArguments(
                "Extraneous arguments passed to {}.".format(rule_name),
            )
    return validate
