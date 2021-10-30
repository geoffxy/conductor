import argparse
import re
import yaml

PROPERTY_REGEX = re.compile("{(?P<property>[a-zA-Z0-9_]+)}")

ERROR_CLASS_TEMPLATE = """class {error_name}(ConductorError):
    error_code = {error_code}

    def __init__(self, **kwargs):
        super().__init__()
{init_body}
    
    def _message(self):
        return "{message}".format(
{message_properties}
        )
"""

PROPERTY_INIT_TEMPLATE = '        self.{property_name} = kwargs["{property_name}"]'

PROPERTY_MESSAGE_TEMPLATE = "            {property_name}=self.{property_name},"

ALL_ERRORS_TEMPLATE = """__all__ = [
{errors}
]
"""

ERROR_ENTRY_TEMPLATE = '    "{error_name}",'


def generate_error_class(error_code, error_properties, output_file):
    name = error_properties["name"]
    message = error_properties["message"]
    properties = PROPERTY_REGEX.findall(message)

    init_properties = "\n".join(
        [
            PROPERTY_INIT_TEMPLATE.format(property_name=property_name)
            for property_name in properties
        ]
    )
    message_properties = "\n".join(
        [
            PROPERTY_MESSAGE_TEMPLATE.format(property_name=property_name)
            for property_name in properties
        ]
    )

    output_file.write("\n\n")
    output_file.write(
        ERROR_CLASS_TEMPLATE.format(
            error_name=name,
            error_code=error_code,
            init_body=init_properties,
            message=message,
            message_properties=message_properties,
        )
    )


def main():
    parser = argparse.ArgumentParser("Conductor errors code generator")
    parser.add_argument("--errors-file", type=str, default="errors.yml")
    parser.add_argument(
        "--output",
        type=str,
        default="../src/conductor/errors/generated.py",
    )
    args = parser.parse_args()

    with open(args.errors_file, encoding="UTF-8") as file:
        raw_errors = yaml.load(file, Loader=yaml.Loader)

    with open(args.output, "w", encoding="UTF-8") as file:
        file.write("from .base import ConductorError\n\n")
        file.write(
            "# NOTE: This file was generated by errors/codegen.py. Do not edit\n"
        )
        file.write("#       the generated code unless you know what you are doing!\n")
        file.write("\n")
        file.write("# pylint: skip-file\n")

        all_errors = []
        for error_code, error_properties in raw_errors.items():
            all_errors.append(error_properties["name"])
            generate_error_class(error_code, error_properties, file)

        error_list = "\n".join(
            [
                ERROR_ENTRY_TEMPLATE.format(error_name=error_name)
                for error_name in all_errors
            ]
        )
        file.write("\n\n")
        file.write(ALL_ERRORS_TEMPLATE.format(errors=error_list))


if __name__ == "__main__":
    main()
