from typing import Dict, Optional

from .combine import Combine
from .environment import Environment
from .group import Group
from .raw import RawTaskType
from .run import RunCommand, RunExperiment

_raw_task_types = [
    RawTaskType(
        name="run_command",
        schema={
            "name": str,
            "run": str,
            "parallelizable": bool,
            "args": list,
            "options": dict,
            "deps": [str],
        },
        defaults={"parallelizable": False, "args": [], "options": {}, "deps": []},
        full_type=RunCommand,
    ),
    RawTaskType(
        name="run_experiment",
        schema={
            "name": str,
            "run": str,
            "parallelizable": bool,
            "args": list,
            "options": dict,
            "deps": [str],
        },
        defaults={"parallelizable": False, "args": [], "options": {}, "deps": []},
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
    RawTaskType(
        name="environment",
        schema={
            "name": str,
            "create": str,
            "start": str,
            "stop": str,
            "destroy": str,
            "project_root": Optional[str],
            "mirrored_files": bool,
        },
        defaults={
            "project_root": None,
            "mirrored_files": False,
        },
        full_type=Environment,
    ),
]

raw_task_types: Dict[str, RawTaskType] = {
    task_type.name: task_type for task_type in _raw_task_types
}
