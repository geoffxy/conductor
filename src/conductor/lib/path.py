import os
import pathlib
from typing import List, Union, Optional

from conductor.config import (
    DEPS_ENV_VARIABLE_NAME,
    DEPS_ENV_PATH_SEPARATOR,
    OUTPUT_ENV_VARIABLE_NAME,
)
from conductor.context import Context
from conductor.task_identifier import TaskIdentifier


def get_deps_paths() -> List[pathlib.Path]:
    """
    Returns a list of the output paths of this task's dependencies.
    """
    if DEPS_ENV_VARIABLE_NAME not in os.environ:
        raise RuntimeError(
            "The {} environment variable was not set. Make sure your code is "
            "being executed by Conductor.".format(DEPS_ENV_VARIABLE_NAME)
        )
    return list(
        map(
            pathlib.Path,
            os.environ[DEPS_ENV_VARIABLE_NAME].split(DEPS_ENV_PATH_SEPARATOR),
        )
    )


def get_output_path() -> pathlib.Path:
    """
    Returns the path where this task's outputs should be stored.
    """
    if OUTPUT_ENV_VARIABLE_NAME not in os.environ:
        raise RuntimeError(
            "The {} environment variable was not set. Make sure your code is "
            "being executed by Conductor.".format(OUTPUT_ENV_VARIABLE_NAME)
        )
    return pathlib.Path(os.environ[OUTPUT_ENV_VARIABLE_NAME])


def in_output_dir(file_path: Union[pathlib.Path, str]) -> pathlib.Path:
    """
    If the current script is being run by Conductor, this function amends
    `file_path` to make it fall under where Conductor's task outputs should be
    stored. Otherwise, this function returns `file_path` unchanged.

    This is meant to be useful for scripts that may be run independently of
    Conductor. Note that `file_path` should be a relative path.
    """
    if OUTPUT_ENV_VARIABLE_NAME in os.environ:
        return get_output_path() / file_path
    elif not isinstance(file_path, pathlib.Path):
        return pathlib.Path(file_path)
    else:
        return file_path


def where(
    identifier: str, relative_to_project_root: bool = False, non_existent_ok: bool = False
) -> Optional[pathlib.Path]:
    """
    Returns the output location path of the given task identifier. If this
    returns `None`, it indicates no output location is available (e.g., the task
    has not run before).

    If `relative_to_project_root` is set to True, this will return a relative
    path to the project root. Otherwise, it returns an absolute path.

    If `non_existent_ok` is set to True, this will return the task's output path
    even if the path does not yet exist.
    """
    ctx = Context.from_cwd()
    task_identifier = TaskIdentifier.from_str(
        identifier,
        require_prefix=False,
    )
    ctx.task_index.load_single_task(task_identifier)
    task = ctx.task_index.get_task(task_identifier)
    output_path = task.get_output_path(ctx)
    if output_path is None or (not output_path.exists() and not non_existent_ok):
        return None
    if relative_to_project_root:
        return output_path.relative_to(ctx.project_root)
    else:
        return output_path
