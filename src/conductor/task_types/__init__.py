from .experiment import RunExperiment
from .raw import RawTaskType

_raw_task_types = [
    RawTaskType(
        "run_experiment",
        {
            "name": str,
            "run": str,
        },
        RunExperiment,
    ),
]

raw_task_types = {
    task_type.name: task_type for task_type in _raw_task_types
}
