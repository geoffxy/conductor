import sys
import traceback

from conductor.context import Context
from conductor.errors import ConductorError


def register_command(subparsers):
    parser = subparsers.add_parser(
        "run",
        help="Run a specific Conductor target.",
    )
    parser.add_argument(
        "task_identifier",
        type=str,
        help="The task that Conductor should run.",
    )
    parser.set_defaults(func=main)


def main(args):
    try:
        context = Context.from_cwd()
        context.run_tasks(args.task_identifier)

    except ConductorError as ex:
        if args.debug:
            print(traceback.format_exc(), file=sys.stderr)
        print("ERROR:", ex.printable_message(), file=sys.stderr)
        sys.exit(1)
