from typing import List, Set

from conductor.execution.ops.operation import Operation
from conductor.task_types.base import TaskType


class ExecutionPlan:
    """
    Represents a plan for executing a task, including its dependencies.
    """

    def __init__(
        self,
        *,
        task_to_run: TaskType,
        all_ops: List[Operation],
        initial_ops: List[Operation],
        cached_tasks: List[TaskType],
        num_tasks_to_run: int,
        used_envs: Set[str],
    ) -> None:
        self.task_to_run = task_to_run
        self.all_ops = all_ops
        self.initial_ops = initial_ops
        self.cached_tasks = cached_tasks
        self.num_tasks_to_run = num_tasks_to_run
        self.used_envs = used_envs

    def reset_waiting_on(self) -> None:
        for op in self.all_ops:
            op.reset_waiting_on()
