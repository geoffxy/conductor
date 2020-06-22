import os
import pathlib
import itertools
import sys
import traceback
from conductor.parsing.parser import Parser
from conductor.task_identifier import TaskIdentifier
from conductor.errors import ConductorError

CONFIG_FILE_NAME = ".condconfig"


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


def find_project_root():
    here = pathlib.Path(os.getcwd())
    for path in itertools.chain([here], here.parents):
        maybe_config_path = path / CONFIG_FILE_NAME
        if maybe_config_path.is_file():
            return path
    raise ConductorError(
        "Could not locate your project's root. Did you add a {} file?"
        .format(CONFIG_FILE_NAME),
    )


def main(args):
    try:
        project_root = find_project_root()
        task_identifier = TaskIdentifier.from_str(
            args.task_identifier,
            require_prefix=False,
        )
        print("Project root:", project_root)
        print("Task identifier:", task_identifier)

        parser = Parser(project_root)
        tasks = parser.parse_cond_file(task_identifier)
        print(tasks)

    except ConductorError as ex:
        if args.debug:
            print(traceback.format_exc(), file=sys.stderr)
        print("ERROR:", ex, file=sys.stderr)
        sys.exit(1)
