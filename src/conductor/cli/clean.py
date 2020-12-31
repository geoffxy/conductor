import os
import shutil
import sys
import traceback

from conductor.config import OUTPUT_DIR
from conductor.context import Context
from conductor.errors import ConductorError
from conductor.user_code_utils import cli_command


def register_command(subparsers):
    parser = subparsers.add_parser(
        "clean",
        help="Remove all Conductor generated files.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Prompt for confirmation before performing the clean operation.",
    )
    parser.set_defaults(func=main)


@cli_command
def main(args):
    ctx = Context.from_cwd()
    generated_files_path = ctx.project_root / OUTPUT_DIR

    if args.interactive:
        try:
            confirm = input(
                "Remove {}? This cannot be undone. [y/N] ".format(
                    str(generated_files_path)
                )
            )
            if confirm.strip().lower() != "y":
                print("Aborting!")
                sys.exit(1)

        except EOFError:
            print()
            print("Aborting!")
            sys.exit(1)

    shutil.rmtree(generated_files_path, ignore_errors=True)
