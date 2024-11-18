from typing import List

from conductor.execution.ops.operation import Operation
from conductor.task_types.base import TaskType


class ExecutionPlan:
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
        num_tasks_to_run: int,
    ) -> None:
        self.task_to_run = task_to_run
        self.all_ops = all_ops
        self.initial_ops = initial_ops
        self.cached_tasks = cached_tasks
        self.num_tasks_to_run = num_tasks_to_run

    def reset_waiting_on(self) -> None:
        for op in self.all_ops:
            op.reset_waiting_on()
