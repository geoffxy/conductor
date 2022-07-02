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
    if output_path is None or not output_path.exists():
        raise NoTaskOutputPath(task_identifier=str(task_identifier))
    print(output_path)
