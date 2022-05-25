import pathlib
import re
import shutil
from typing import List

from conductor.context import Context
from conductor.utils.user_code import cli_command
from conductor.task_identifier import TaskIdentifier

_EXPERIMENT_TASK_REGEX = re.compile(
    r"^(?P<name>[a-zA-Z0-9_-]+)\.task\.(?P<timestamp>[1-9][0-9]*)$"
)

_REGULAR_TASK_REGEX = re.compile(r"^(?P<name>[a-zA-Z0-9_-]+)\.task$")


def register_command(subparsers):
    parser = subparsers.add_parser(
        "gc",
        help="Removes failed experiment task outputs.",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Set this flag to have Conductor print the directories it would delete "
        "instead of actually deleting them.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Set this flag to have Conductor print the directories it is deleting as "
        "they are deleted.",
    )
    parser.set_defaults(func=main)


@cli_command
def main(args):
    ctx = Context.from_cwd()
    all_versions_list = ctx.version_index.get_all_versions()
    all_versions = {
        (identifier, version.timestamp) for identifier, version in all_versions_list
    }

    output_path = ctx.output_path
    cwd = pathlib.Path.cwd()
    assert output_path.is_absolute()
    stack = [output_path]
    while len(stack) > 0:
        curr_path = stack.pop()
        to_delete: List[pathlib.Path] = []

        for inner in curr_path.iterdir():
            if not inner.is_dir():
                continue
            exp_match = _EXPERIMENT_TASK_REGEX.match(inner.name)
            if exp_match is None:
                if _REGULAR_TASK_REGEX.match(inner.name) is None:
                    # If this directory is not a Conductor task directory, we
                    # should "explore" it.
                    stack.append(inner)
                continue

            # Check if this experiment directory is in the index. If not, it
            # should be deleted.
            task_name = exp_match.group("name")
            timestamp = int(exp_match.group("timestamp"))
            task_path = inner.parent.relative_to(output_path)
            task_identifier = TaskIdentifier(task_path, task_name)

            if (task_identifier, timestamp) not in all_versions:
                to_delete.append(inner)

        if args.dry_run:
            for exp_path in to_delete:
                print("Would delete", str(exp_path.relative_to(cwd)))
        else:
            for exp_path in to_delete:
                if args.verbose:
                    print("Deleting", str(exp_path.relative_to(cwd)))
                shutil.rmtree(exp_path, ignore_errors=True)
