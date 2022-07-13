from conductor.context import Context
from conductor.errors import NoTaskOutputPath
from conductor.task_identifier import TaskIdentifier
from conductor.utils.user_code import cli_command


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
    ctx = Context.from_cwd()
    task_identifier = TaskIdentifier.from_str(
        args.task_identifier,
        require_prefix=False,
    )
    ctx.task_index.load_single_task(task_identifier)
    task = ctx.task_index.get_task(task_identifier)
    output_path = task.get_output_path(ctx)
    if output_path is None or (not output_path.exists() and not args.non_existent_ok):
        raise NoTaskOutputPath(task_identifier=str(task_identifier))
    if args.project:
        print(output_path.relative_to(ctx.project_root))
    else:
        print(output_path)
