from typing import Any, Callable, Dict, Union, get_origin, get_args

from conductor.errors import (
    InvalidTaskParameterType,
    MissingTaskParameter,
    UnrecognizedTaskParameters,
)


def generate_type_validator(
    task_type_name: str, schema: Dict
) -> Callable[[Dict[str, Any]], None]:
    def validate(arguments: Dict[str, Any]) -> None:
        for parameter, type_class in schema.items():
            # 1. If we do not find the parameter (and it is not marked
            # `Optional`), it's an error
            if parameter not in arguments:
                if _is_optional(type_class):
                    # Optional value not included.
                    continue
                raise MissingTaskParameter(
                    parameter_name=parameter,
                    task_type_name=task_type_name,
                )

            # Get the "inner type" if it is optional.
            if _is_optional(type_class):
                if arguments[parameter] is None:
                    # Optional value is `None`.
                    continue
                expected_type = get_args(type_class)
            else:
                expected_type = type_class

            # 2. For lists, we need to check that its contents are all a
            #    predefined type
            if isinstance(expected_type, list):
                if not isinstance(arguments[parameter], list):
                    raise InvalidTaskParameterType(
                        parameter_name=parameter,
                        type_name=list.__name__,
                        task_type_name=task_type_name,
                    )

                item_valid = map(
                    # pylint: disable=cell-var-from-loop
                    lambda el: isinstance(el, expected_type[0]),
                    arguments[parameter],
                )

                if not all(item_valid):
                    raise InvalidTaskParameterType(
                        parameter_name="{}[...]".format(parameter),
                        type_name=type_class[0].__name__,
                        task_type_name=task_type_name,
                    )

            # 3. Otherwise, just check the parameter type
            elif not isinstance(arguments[parameter], expected_type):
                raise InvalidTaskParameterType(
                    parameter_name=parameter,
                    type_name=(
                        type_class.__name__
                        if hasattr(type_class, "__name__")
                        else repr(type_class)
                    ),
                    task_type_name=task_type_name,
                )

        # 4. Ensure that no extraneous arguments are passed in
        for arg in arguments:
            if arg not in schema:
                raise UnrecognizedTaskParameters(task_type_name=task_type_name)

    return validate


def _is_optional(field):
    return get_origin(field) is Union and type(None) in get_args(field)
