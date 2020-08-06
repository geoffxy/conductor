from .experiment import RunExperiment
from .raw import RawTaskType

_raw_task_types = [
    RawTaskType(
        name="run_experiment",
        schema={"name": str, "run": str, "deps": [str], "out": [str]},
        defaults={"deps": [], "out": []},
        full_type=RunExperiment,
    ),
]

raw_task_types = {
    task_type.name: task_type for task_type in _raw_task_types
}
