import enum
from typing import Optional, List
from pydantic import BaseModel

import conductor.task_identifier as ci
import conductor.task_types.base as ct
from conductor.task_types.combine import Combine
from conductor.task_types.group import Group
from conductor.task_types.run import RunExperiment, RunCommand
from conductor.execution.version_index import Version


class TaskType(enum.Enum):
    RunExperiment = "run_experiment"
    RunCommand = "run_command"
    Group = "group"
    Combine = "combine"

    @classmethod
    def from_cond(cls, task_type: ct.TaskType) -> "TaskType":
        if isinstance(task_type, RunExperiment):
            return cls.RunExperiment
        elif isinstance(task_type, RunCommand):
            return cls.RunCommand
        elif isinstance(task_type, Group):
            return cls.Group
        elif isinstance(task_type, Combine):
            return cls.Combine
        else:
            raise ValueError(f"Unknown task type: {task_type}")


class TaskIdentifier(BaseModel):
    path: str
    name: str

    @classmethod
    def from_cond(cls, identifier: ci.TaskIdentifier) -> "TaskIdentifier":
        return cls(path=str(identifier.path), name=identifier.name)

    @property
    def display(self) -> str:
        return f"//{self.path}/{self.name}"


class ResultVersion(BaseModel):
    timestamp: int
    commit_hash: Optional[str]
    has_uncommitted_changes: bool

    @classmethod
    def from_version(cls, version: Version) -> "ResultVersion":
        return cls(
            timestamp=version.timestamp,
            commit_hash=version.commit_hash,
            has_uncommitted_changes=version.has_uncommitted_changes,
        )


class TaskResults(BaseModel):
    identifier: TaskIdentifier
    versions: List[ResultVersion]


class Task(BaseModel):
    task_type: TaskType
    identifier: TaskIdentifier
    deps: List[TaskIdentifier]


class TaskGraph(BaseModel):
    tasks: List[Task]
    # These are tasks that have no dependees.
    root_tasks: List[TaskIdentifier]
