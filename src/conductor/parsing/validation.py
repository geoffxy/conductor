from typing import Any, Callable, Dict

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
            # 1. If we do not find the parameter, it's an error
            if parameter not in arguments:
                raise MissingTaskParameter(
                    parameter_name=parameter,
                    task_type_name=task_type_name,
                )

            # 2. For lists, we need to check that its contents are all a
            #    predefined type
            if isinstance(type_class, list):
                if not isinstance(arguments[parameter], list):
                    raise InvalidTaskParameterType(
                        parameter_name=parameter,
                        type_name=list.__name__,
                        task_type_name=task_type_name,
                    )

                item_valid = map(
                    # pylint: disable=cell-var-from-loop
                    lambda el: isinstance(el, type_class[0]),
                    arguments[parameter],
                )

                if not all(item_valid):
                    raise InvalidTaskParameterType(
                        parameter_name="{}[...]".format(parameter),
                        type_name=type_class[0].__name__,
                        task_type_name=task_type_name,
                    )

            # 3. Otherwise, just check the parameter type
            elif not isinstance(arguments[parameter], type_class):
                raise InvalidTaskParameterType(
                    parameter_name=parameter,
                    type_name=type_class.__name__,
                    task_type_name=task_type_name,
                )

        # 4. Ensure that no extraneous arguments are passed in
        if len(arguments) != len(schema):
            raise UnrecognizedTaskParameters(task_type_name=task_type_name)

    return validate
