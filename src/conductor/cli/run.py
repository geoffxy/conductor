import os
import pathlib
import itertools
import sys
import traceback
from conductor.target_name import TargetName

CONFIG_FILE_NAME = ".condconfig"


def register_command(subparsers):
    parser = subparsers.add_parser(
        "run",
        help="Run a specific Conductor target.",
    )
    parser.add_argument(
        "target",
        type=str,
        help="The target that Conductor should run.",
    )
    parser.set_defaults(func=main)


def find_project_root():
    here = pathlib.Path(os.getcwd())
    for path in itertools.chain([here], here.parents):
        maybe_config_path = path / CONFIG_FILE_NAME
        if maybe_config_path.is_file():
            return path
    raise RuntimeError(
        "Could not locate your project's root. Did you add a {} file?"
        .format(CONFIG_FILE_NAME),
    )


def main(args):
    try:
        project_root = find_project_root()
        target_name = TargetName.from_str(args.target, require_prefix=False)
        print("Project root:", project_root)
        print("Target name:", target_name)

    except RuntimeError as ex:
        if args.debug:
            print(traceback.format_exc(), file=sys.stderr)
        print("ERROR:", ex, file=sys.stderr)
