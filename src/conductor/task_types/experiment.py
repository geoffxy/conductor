import subprocess

from conductor.task_types.base import TaskType
from conductor.config import OUTPUT_ENV_VARIABLE_NAME


class RunExperiment(TaskType):
    def __init__(self, identifier, run):
        super().__init__(identifier=identifier)
        self._run = run

    def __repr__(self):
        return "".join([super().__repr__(), ", run=", self._run, ")"])

    def execute(self, project_root):
        process = subprocess.Popen(
            [self._run],
            shell=True,
            cwd=self._get_working_path(project_root),
            env={
                OUTPUT_ENV_VARIABLE_NAME:
                    self._get_and_prepare_output_path(project_root),
            },
        )
        process.wait()
