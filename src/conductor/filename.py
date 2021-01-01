from typing import Optional

from conductor.config import ARCHIVE_FILE_NAME_TEMPLATE, TASK_OUTPUT_DIR_SUFFIX
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier


def archive(timestamp: str) -> str:
    return ARCHIVE_FILE_NAME_TEMPLATE.format(timestamp=timestamp)


def task_output_dir(
    task_identifier: TaskIdentifier, version: Optional[Version] = None
) -> str:
    if version is None:
        return task_identifier.name + TASK_OUTPUT_DIR_SUFFIX
    else:
        return "{}{}.{}".format(
            task_identifier.name, TASK_OUTPUT_DIR_SUFFIX, str(version)
        )
