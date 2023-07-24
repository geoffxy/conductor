import os
import pathlib
from typing import List, Union

from conductor.config import (
    DEPS_ENV_VARIABLE_NAME,
    DEPS_ENV_PATH_SEPARATOR,
    OUTPUT_ENV_VARIABLE_NAME,
)


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
