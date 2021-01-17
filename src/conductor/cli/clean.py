import shutil
import sys

from conductor.context import Context
from conductor.utils.user_code import cli_command


def register_command(subparsers):
    parser = subparsers.add_parser(
        "clean",
        help="Remove all Conductor generated files.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Do not prompt for confirmation before performing the clean operation. "
        "Use with caution! The clean operation cannot be undone.",
    )
    parser.set_defaults(func=main)


@cli_command
def main(args):
    ctx = Context.from_cwd()

    if not args.force:
        try:
            confirm = input(
                "Remove {}? This cannot be undone. [y/N] ".format(str(ctx.output_path))
            )
            if confirm.strip().lower() != "y":
                print("Aborting!")
                sys.exit(1)

        except EOFError:
            print()
            print("Aborting!")
            sys.exit(1)

    shutil.rmtree(ctx.output_path, ignore_errors=True)
