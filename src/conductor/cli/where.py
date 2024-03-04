from conductor.errors import NoTaskOutputPath
from conductor.utils.user_code import cli_command
from conductor.lib.path import where


def register_command(subparsers):
    parser = subparsers.add_parser(
        "where",
        help="Prints the output path of a task.",
    )
    parser.add_argument(
        "task_identifier",
        type=str,
        help="The task whose output path to print.",
    )
    parser.add_argument(
        "-p",
        "--project",
        action="store_true",
        help="If set, Conductor will print the output path relative to the project "
        "root.",
    )
    parser.add_argument(
        "-f",
        "--non-existent-ok",
        action="store_true",
        help="If set, Conductor will print the output path even if it does not exist "
        "yet. This flag only has an effect for tasks that have deterministic output "
        "paths (e.g., run_command() or combine()).",
    )
    parser.set_defaults(func=main)


@cli_command
def main(args):
    result = where(
        args.task_identifier,
        relative_to_project_root=args.project,
        non_existent_ok=args.non_existent_ok,
    )
    if result is None:
        raise NoTaskOutputPath(task_identifier=args.task_identifier)
    print(result)
