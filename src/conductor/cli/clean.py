import os
import shutil
import sys
import traceback

from conductor.config import OUTPUT_DIR
from conductor.context import Context
from conductor.errors import ConductorError


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


def main(args):
    try:
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

    except ConductorError as ex:
        if args.debug:
            print(traceback.format_exc(), file=sys.stderr)
        print("ERROR:", ex.printable_message(), file=sys.stderr)
        sys.exit(1)
