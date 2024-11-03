from typing import List

from conductor.execution.ops.operation import Operation
from conductor.task_types.base import TaskType


class ExecutionPlan2:
    """
    Represents a plan for executing a task, including its dependencies.
    """

    # NOTE: This will replace `ExecutionPlan` after the refactor.

    def __init__(
        self,
        *,
        task_to_run: TaskType,
        all_ops: List[Operation],
        initial_ops: List[Operation],
        cached_tasks: List[TaskType],
    ) -> None:
        self.task_to_run = task_to_run
        self.all_ops = all_ops
        self.initial_ops = initial_ops
        self.cached_tasks = cached_tasks
