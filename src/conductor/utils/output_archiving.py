import pathlib
import subprocess
import shutil
import sqlite3
from typing import List, Optional, Tuple

import conductor.filename as f
from conductor.config import ARCHIVE_VERSION_INDEX, ARCHIVE_STAGING
from conductor.context import Context
from conductor.errors import (
    InternalError,
    CreateArchiveFailed,
    ArchiveFileInvalid,
    DuplicateTaskOutput,
)
from conductor.execution.version_index import VersionIndex, Version
from conductor.task_identifier import TaskIdentifier


def create_archive(
    ctx: Context,
    tasks_to_archive: List[Tuple[TaskIdentifier, Optional[Version]]],
    output_archive_path: pathlib.Path,
) -> None:
    """
    This utility is used to create an archive of the output directories of the
    given tasks for transport purposes (e.g., moving data to/from a remote
    environment).
    """

    # Ensure versions are specified when they should be specified.
    # Partition tasks into versioned and unversioned tasks.
    versioned_tasks = []
    unversioned_tasks = []
    for task_id, version in tasks_to_archive:
        task = ctx.task_index.get_task(task_id)
        if task.archivable:
            if version is None:
                raise InternalError(
                    details=f"Did not provide a version for an archivable task {str(task_id)}."
                )
            versioned_tasks.append((task_id, version))
        else:
            unversioned_tasks.append(task_id)

    try:
        archive_index_path = ctx.output_path / ARCHIVE_VERSION_INDEX
        archive_index_path.unlink(missing_ok=True)

        # Store the versions of the tasks that are being archived.
        archive_index = VersionIndex.create_or_load(
            ctx.output_path / ARCHIVE_VERSION_INDEX
        )
        VersionIndex.copy_specific_entries_to(archive_index, versioned_tasks)
        archive_index.bulk_load_unversioned(unversioned_tasks)
        archive_index.commit_changes()

        # Collect the output directories for the tasks to archive.
        output_dirs_str = []
        for task_id, version in versioned_tasks:
            output_dirs_str.append(
                str(
                    pathlib.Path(
                        task_id.path,
                        f.task_output_dir(task_id, version),
                    )
                )
            )
        for task_id in unversioned_tasks:
            output_dirs_str.append(
                str(pathlib.Path(task_id.path, f.task_output_dir(task_id)))
            )

        # Create the archive.
        process = subprocess.Popen(
            [
                "tar",
                "-cf",
                str(output_archive_path),
                f"--use-compress-program={_compress_program(output_archive_path)}",
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

    finally:
        # Clean up the archive index file.
        archive_index_path.unlink(missing_ok=True)


def restore_archive(ctx: Context, archive_path: pathlib.Path) -> None:
    """
    This utility is used to restore the output directories of tasks from an
    archive created by `create_archive`.
    """

    try:
        # Extract the archive to a staging location.
        staging_path = ctx.output_path / ARCHIVE_STAGING
        staging_path.mkdir(parents=True, exist_ok=True)
        _extract_archive(archive_path, staging_path)

        # Load the archive version index.
        archive_version_index_path = staging_path / ARCHIVE_VERSION_INDEX
        archive_version_index = VersionIndex.create_or_load(archive_version_index_path)

        # Transfer the version index entries to the current version index.
        try:
            archive_version_index.copy_entries_to(
                dest=ctx.version_index, tasks=None, latest_only=False
            )
        except sqlite3.IntegrityError as ex:
            raise DuplicateTaskOutput(output_dir=str(ctx.output_path)) from ex

        # Copy over versioned tasks.
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

        # Copy over unversioned tasks.
        for task_id in archive_version_index.get_all_unversioned():
            src_task_path = pathlib.Path(
                staging_path, task_id.path, f.task_output_dir(task_id)
            )
            if not src_task_path.is_dir():
                raise ArchiveFileInvalid().add_extra_context(
                    "Missing archived task output for '{}' in the "
                    "archive.".format(str(task_id))
                )

            dest_task_path = pathlib.Path(
                ctx.output_path, task_id.path, f.task_output_dir(task_id)
            )
            dest_task_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_task_path, dest_task_path)
            if not dest_task_path.is_dir():
                raise ArchiveFileInvalid().add_extra_context(
                    "Missing copied archived task output for '{}'.".format(str(task_id))
                )

        # Safe to commit now.
        ctx.version_index.commit_changes()

    except:
        # Something went wrong, so undo our changes.
        ctx.version_index.rollback_changes()
        raise

    finally:
        # Clean up the staging directory.
        shutil.rmtree(staging_path, ignore_errors=True)


def _extract_archive(archive_file: pathlib.Path, staging_path: pathlib.Path):
    try:
        process = subprocess.Popen(
            [
                "tar",
                "-xf",
                str(archive_file),
                f"--use-compress-program={_compress_program(archive_file)}",
                "-C",
                str(staging_path),
            ],
            shell=False,
        )
        process.wait()
        if process.returncode != 0:
            raise ArchiveFileInvalid().add_extra_context(
                "The tar utility returned a non-zero error code."
            )

    except OSError as ex:
        raise ArchiveFileInvalid().add_extra_context(str(ex))


def _compress_program(archive_file: pathlib.Path) -> str:
    if archive_file.suffix == ".gz":
        # This is a heuristic we use to support legacy Conductor archives (which
        # were gzip-compressed).
        return "gzip"
    else:
        # Conductor has switched to using zstd for compression.
        return "zstdmt"
