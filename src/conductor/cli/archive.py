import pathlib
import datetime
import subprocess
from typing import List, Optional

import conductor.filename as f
from conductor.config import ARCHIVE_VERSION_INDEX
from conductor.context import Context
from conductor.errors import (
    CreateArchiveFailed,
    OutputFileExists,
    OutputPathDoesNotExist,
    NoTaskOutputsToArchive,
)
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType
from conductor.execution.version_index import VersionIndex
from conductor.utils.user_code import cli_command


def register_command(subparsers):
    parser = subparsers.add_parser(
        "archive",
        help="Create an archive of task outputs.",
    )
    parser.add_argument(
        "task_identifier",
        type=str,
        nargs="?",
        help="The task that Conductor should archive. If unspecified, Conductor will "
        "archive all archivable task outputs.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="The path (and optionally file name) where the output archive should be "
        "saved. The path must exist. If unspecified, Conductor will save the archive "
        "in its output directory.",
    )
    parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="If set, Conductor will only archive the latest output version of the "
        "requested task(s). By default, Conductor will archive all output versions of "
        "the archivable tasks.",
    )
    parser.set_defaults(func=main)


def generate_archive_name() -> str:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d+%H-%M-%S")
    return f.archive(timestamp=timestamp)


def handle_output_path(ctx: Context, raw_output_path: Optional[str]) -> pathlib.Path:
    if raw_output_path is None:
        output_path = pathlib.Path(
            ctx.output_path,
            generate_archive_name(),
        )
        return output_path

    # Validate the output path. It can either be a path to a directory (which
    # must exist), or a path with a file name for the archive. If it is a path
    # with a file name for the archive, the archive's parent directory must exist.
    output_path = pathlib.Path(raw_output_path)
    if output_path.exists():
        if output_path.is_dir():
            # Corresponds to the case where the user provides a path to a
            # directory where the archive should be stored
            return output_path / generate_archive_name()
        raise OutputFileExists()

    elif output_path.parent.exists() and output_path.parent.is_dir():
        # Corresponds to the case where the user provides a full path that
        # includes the desired archive file name
        return output_path

    raise OutputPathDoesNotExist()


def compute_tasks_to_archive(
    ctx: Context, raw_task_identifier: Optional[str]
) -> Optional[List[TaskIdentifier]]:
    if raw_task_identifier is None:
        return None

    task_identifier = TaskIdentifier.from_str(
        raw_task_identifier,
        require_prefix=False,
    )
    ctx.task_index.load_transitive_closure(task_identifier)

    relevant_tasks = []

    def append_if_archivable(task: TaskType):
        if not task.archivable:
            return
        relevant_tasks.append(task.identifier)

    root_task = ctx.task_index.get_task(task_identifier)
    root_task.traverse(ctx, append_if_archivable)
    return relevant_tasks


def create_archive(
    ctx: Context,
    archive_index: VersionIndex,
    output_archive_path: pathlib.Path,
    archive_index_path: pathlib.Path,
) -> None:
    output_dirs_str = [
        str(
            pathlib.Path(
                task_id.path,
                f.task_output_dir(task_id, version),
            )
        )
        for task_id, version in archive_index.get_all_versions()
    ]

    try:
        process = subprocess.Popen(
            [
                "tar",
                "czf",  # Create a new archive and use gzip to compress
                str(output_archive_path),
                "-C",  # Files to put in the archive are relative to `ctx.output_path`
                str(ctx.output_path),
                str(archive_index_path.relative_to(ctx.output_path)),
                *output_dirs_str,
            ],
            shell=False,
        )
        process.wait()
        if process.returncode != 0:
            raise CreateArchiveFailed().add_extra_context(
                "The tar utility returned a non-zero error code."
            )

    except OSError as ex:
        raise CreateArchiveFailed().add_extra_context(str(ex))


@cli_command
def main(args):
    ctx = Context.from_cwd()
    output_archive_path = handle_output_path(ctx, args.output)

    # If `None`, we should archive all tasks
    tasks_to_archive = compute_tasks_to_archive(ctx, args.task_identifier)
    if tasks_to_archive is not None and len(tasks_to_archive) == 0:
        raise NoTaskOutputsToArchive()

    try:
        archive_index_path = pathlib.Path(ctx.output_path, ARCHIVE_VERSION_INDEX)
        archive_index_path.unlink(missing_ok=True)
        archive_index = VersionIndex.create_or_load(archive_index_path)
        total_entry_count = ctx.version_index.copy_entries_to(
            dest=archive_index, tasks=tasks_to_archive, latest_only=args.latest
        )
        if total_entry_count == 0:
            raise NoTaskOutputsToArchive()

        archive_index.commit_changes()
        create_archive(ctx, archive_index, output_archive_path, archive_index_path)

        # Compute a relative path to the current working directory, if possible
        try:
            relative_output_path = output_archive_path.relative_to(pathlib.Path.cwd())
        except ValueError:
            relative_output_path = output_archive_path
        print("✨ Done! Archive saved as", str(relative_output_path))

    except:
        output_archive_path.unlink(missing_ok=True)
        raise

    finally:
        archive_index_path.unlink(missing_ok=True)
