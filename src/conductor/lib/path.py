import os
import pathlib
from typing import List

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
