from typing import Dict

from .combine import Combine
from .group import Group
from .raw import RawTaskType
from .run import RunCommand, RunExperiment

_raw_task_types = [
    RawTaskType(
        name="run_command",
        schema={"name": str, "run": str, "deps": [str]},
        defaults={"deps": []},
        full_type=RunCommand,
    ),
    RawTaskType(
        name="run_experiment",
        schema={"name": str, "run": str, "options": dict, "deps": [str]},
        defaults={"options": {}, "deps": []},
        full_type=RunExperiment,
    ),
    RawTaskType(
        name="group",
        schema={"name": str, "deps": [str]},
        defaults={"deps": []},
        full_type=Group,
    ),
    RawTaskType(
        name="combine",
        schema={"name": str, "deps": [str]},
        defaults={"deps": []},
        full_type=Combine,
    ),
]

raw_task_types: Dict[str, RawTaskType] = {
    task_type.name: task_type for task_type in _raw_task_types
}
