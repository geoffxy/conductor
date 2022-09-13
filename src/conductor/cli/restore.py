import pathlib
import subprocess
import shutil
import sqlite3

import conductor.filename as f
from conductor.config import ARCHIVE_STAGING, ARCHIVE_VERSION_INDEX
from conductor.context import Context
from conductor.errors import ArchiveFileInvalid, DuplicateTaskOutput
from conductor.execution.version_index import VersionIndex
from conductor.utils.user_code import cli_command


def register_command(subparsers):
    parser = subparsers.add_parser(
        "restore",
        help="Restore previously archived task outputs.",
    )
    parser.add_argument(
        "archive_file",
        type=str,
        help="Path to the archive file to restore.",
    )
    parser.set_defaults(func=main)


def extract_archive(archive_file: pathlib.Path, staging_path: pathlib.Path):
    try:
        process = subprocess.Popen(
            ["tar", "xzf", str(archive_file), "-C", str(staging_path)],
            shell=False,
        )
        process.wait()
        if process.returncode != 0:
            raise ArchiveFileInvalid().add_extra_context(
                "The tar utility returned a non-zero error code."
            )

    except OSError as ex:
        raise ArchiveFileInvalid().add_extra_context(str(ex))


@cli_command
def main(args):
    ctx = Context.from_cwd()

    archive_file = pathlib.Path(args.archive_file)
    if not archive_file.is_file():
        raise ArchiveFileInvalid()

    try:
        archive_version_index = None
        staging_path = ctx.output_path / ARCHIVE_STAGING
        staging_path.mkdir(exist_ok=True)
        extract_archive(archive_file, staging_path)

        archive_version_index_path = staging_path / ARCHIVE_VERSION_INDEX
        if not archive_version_index_path.is_file():
            raise ArchiveFileInvalid().add_extra_context(
                "Could not locate the archive version index."
            )

        archive_version_index = VersionIndex.create_or_load(archive_version_index_path)
        try:
            archive_version_index.copy_entries_to(
                dest=ctx.version_index, tasks=None, latest_only=False
            )
        except sqlite3.IntegrityError as ex:
            raise DuplicateTaskOutput(output_dir=str(ctx.output_path)) from ex

        # Copy over all archived task outputs
        for task_id, version in archive_version_index.get_all_versions():
            src_task_path = pathlib.Path(
                staging_path, task_id.path, f.task_output_dir(task_id, version)
            )
            if not src_task_path.is_dir():
                raise ArchiveFileInvalid().add_extra_context(
                    "Missing archived task output for '{}' at version {} in the "
                    "archive.".format(str(task_id), str(version))
                )

            dest_task_path = pathlib.Path(
                ctx.output_path, task_id.path, f.task_output_dir(task_id, version)
            )
            dest_task_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_task_path, dest_task_path)
            if not dest_task_path.is_dir():
                raise ArchiveFileInvalid().add_extra_context(
                    "Missing copied archived task output for '{}' at version {}.".format(
                        str(task_id), str(version)
                    )
                )

        # Everything was copied over and verified - safe to commit the index changes
        ctx.version_index.commit_changes()

    except:
        ctx.version_index.rollback_changes()
        raise

    finally:
        del archive_version_index
        shutil.rmtree(staging_path, ignore_errors=True)
