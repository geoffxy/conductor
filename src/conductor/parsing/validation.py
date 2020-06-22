from conductor.errors import InvalidTaskArguments


def _invalid_argument_type(parameter, expected_type):
    return InvalidTaskArguments(
        "Invalid type for argument '{}' (expected {}).".format(
            parameter,
            expected_type.__name__,
        ),
    )


def generate_type_validator(task_type_name, schema):
    def validate(arguments):
        for parameter, type_class in schema.items():
            # 1. If we do not find the parameter, it's an error
            if parameter not in arguments:
                raise InvalidTaskArguments(
                    "Missing '{}' argument in {}.".format(
                        parameter,
                        task_type_name,
                    ),
                )

            # 2. For lists, we need to check that its contents are all a
            #    predefined type
            if isinstance(type_class, list):
                if not isinstance(arguments[parameter], list):
                    raise _invalid_argument_type(parameter, list)

                item_valid = map(
                    lambda el: isinstance(el, type_class[0]),
                    arguments[parameter],
                )

                if not all(item_valid):
                    raise _invalid_argument_type(
                        "{}[...]".format(parameter),
                        type_class[0],
                    )

            # 3. Otherwise, just check the parameter type
            elif not isinstance(arguments[parameter], type_class):
                raise _invalid_argument_type(parameter, type_class)

        # 4. Ensure that no extraneous arguments are passed in
        if len(arguments) != len(schema):
            raise InvalidTaskArguments(
                "Extraneous arguments passed to {}.".format(task_type_name),
            )

    return validate
