import subprocess

from conductor.task_types.base import TaskType
from conductor.config import (
    OUTPUT_ENV_VARIABLE_NAME,
    DEPS_ENV_VARIABLE_NAME,
    DEPS_ENV_PATH_SEPARATOR,
)


class RunCommand(TaskType):
    def __init__(self, identifier, cond_file_path, deps, run):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps
        )
        self._run = run

    def __repr__(self):
        return "".join(
            [
                super().__repr__(),
                ", run=",
                self._run,
                ")",
            ]
        )

    def execute(self, project_root, task_index):
        process = subprocess.Popen(
            [self._run],
            shell=True,
            cwd=self._get_working_path(project_root),
            env={
                OUTPUT_ENV_VARIABLE_NAME: self.get_and_prepare_output_path(
                    project_root
                ),
                DEPS_ENV_VARIABLE_NAME: DEPS_ENV_PATH_SEPARATOR.join(
                    map(str, self.get_deps_output_paths(project_root, task_index))
                ),
            },
        )
        process.wait()


class RunExperiment(RunCommand):
    def __init__(self, identifier, cond_file_path, deps, run):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps, run=run
        )
