from conductor.task_types.base import BaseTaskType


class RunExperiment(BaseTaskType):
    def __init__(self, name, run):
        super().__init__(name=name)
        self.run = run
