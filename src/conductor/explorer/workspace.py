from typing import List, Optional
from conductor.task_identifier import TaskIdentifier


class Workspace:
    """
    Used to cache useful state used by our explorer APIs.
    """

    def __init__(self) -> None:
        self._root_task_ids: Optional[List[TaskIdentifier]] = None

    def clear(self) -> None:
        self._root_task_ids = None

    @property
    def root_task_ids(self) -> Optional[List[TaskIdentifier]]:
        return self._root_task_ids

    def set_root_task_ids(self, root_task_ids: List[TaskIdentifier]) -> None:
        self._root_task_ids = root_task_ids
