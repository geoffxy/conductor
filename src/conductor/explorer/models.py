import enum
import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel

import conductor.task_identifier as ci
import conductor.task_types.base as ct
from conductor.task_types.combine import Combine
from conductor.task_types.group import Group
from conductor.task_types.run import RunExperiment, RunCommand
from conductor.execution.version_index import Version
from conductor.utils.git import Git


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
    is_override: bool

    @classmethod
    def from_version(cls, version: Version) -> "ResultVersion":
        return cls(
            timestamp=version.timestamp,
            commit_hash=version.commit_hash,
            has_uncommitted_changes=version.has_uncommitted_changes,
            is_override=version.is_override,
        )


class TaskResults(BaseModel):
    identifier: TaskIdentifier
    versions: List[ResultVersion]
    current_version: Optional[ResultVersion] = None


class TaskRunnableDetails(BaseModel):
    run: str
    args: List[str]
    options: Dict[str, str]


class Task(BaseModel):
    task_type: TaskType
    identifier: TaskIdentifier
    deps: List[TaskIdentifier]
    runnable_details: Optional[TaskRunnableDetails] = None


class TaskGraph(BaseModel):
    tasks: List[Task]
    # These are tasks that have no dependees.
    root_tasks: List[TaskIdentifier]


class VersionGraphNode(BaseModel):
    commit_hash: str
    commit_short_message: Optional[str] = None
    # If this is empty, it means we've kept the commit to provide
    # structure/context in the graph (e.g., it's an ancestor or fork point), but
    # there are no versions that directly reference this commit.
    versions: List[ResultVersion]


class VersionGraphEdge(BaseModel):
    from_commit_hash: str
    to_commit_hash: str


class VersionGraph(BaseModel):
    task_id: TaskIdentifier
    current_commit: Optional[str]
    selected_version: Optional[ResultVersion]
    nodes: List[VersionGraphNode]
    edges: List[VersionGraphEdge]


class CommitInfo(BaseModel):
    commit_hash: str
    date: datetime.datetime
    message: List[str]
    lines_added: int
    lines_removed: int

    @classmethod
    def from_cond(cls, commit: "Git.DetailedCommit") -> "CommitInfo":
        return cls(
            commit_hash=commit.hash,
            date=commit.date,
            message=commit.message,
            lines_added=commit.lines_added,
            lines_removed=commit.lines_removed,
        )
