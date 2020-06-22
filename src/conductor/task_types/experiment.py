from conductor.task_types.base import TaskType


class RunExperiment(TaskType):
    def __init__(self, identifier, run):
        super().__init__(identifier=identifier)
        self._run = run

    def __repr__(self):
        return "".join([super().__repr__(), ", run=", self._run, ")"])

    def execute(self):
        pass
