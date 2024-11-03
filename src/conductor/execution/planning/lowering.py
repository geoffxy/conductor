import enum
from typing import List

from conductor.task_types.base import TaskType
from conductor.execution.ops.operation import Operation


class LoweringState(enum.Enum):
    FIRST_VISIT = 0
    SECOND_VISIT = 1


class LoweringTask:
    """
    This class is used to track metadata about a task while we are converting
    (lowering) a task graph into an operation graph.
    """

    @classmethod
    def initial(cls, task: TaskType) -> "LoweringTask":
        return cls(task, LoweringState.FIRST_VISIT)

    def __init__(self, task: TaskType, state: LoweringState):
        self.task = task
        self.state = state

        # A list of tasks that this task depends on.
        self.deps: List["LoweringTask"] = []

        # The "final" `Operation`s that represent this task. A task can be
        # convered into more than one operation; tasks that depend on this task
        # should take a dependency on these operations.
        self.output_ops: List[Operation] = []
