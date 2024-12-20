import pathlib
import subprocess
from typing import List, Optional, Tuple

import conductor.filename as f
from conductor.config import ARCHIVE_VERSION_INDEX
from conductor.context import Context
from conductor.errors import InternalError, CreateArchiveFailed
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
                "--use-compress-program=zstdmt",
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
