from typing import Dict, Iterable, NamedTuple, Optional, Sequence
from conductor.utils.experiment_options import OptionValue
from conductor.errors import (
    ExperimentGroupDuplicateName,
    ExperimentGroupInvalidExperimentInstance,
)


class ExperimentInstance(NamedTuple):
    name: str
    options: Dict[str, OptionValue]


def run_experiment_group(
    name: str,
    run: str,
    experiments: Iterable[ExperimentInstance],
    deps: Optional[Sequence[str]] = None,
) -> None:
    task_deps = deps if deps is not None else []
    relative_experiment_identifiers = []

    try:
        seen_experiment_names = set()
        for experiment in experiments:
            if not isinstance(experiment, ExperimentInstance):
                raise ExperimentGroupInvalidExperimentInstance(task_name=name)
            if experiment.name in seen_experiment_names:
                raise ExperimentGroupDuplicateName(
                    task_name=name, instance_name=experiment.name
                )

            seen_experiment_names.add(experiment.name)
            # run_experiment(): Defined by Conductor at runtime
            # pylint: disable=undefined-variable
            run_experiment(  # type: ignore
                name=experiment.name,
                run=run,
                options=experiment.options,
                deps=task_deps,
            )
            relative_experiment_identifiers.append(":" + experiment.name)

    except TypeError as ex:
        raise ExperimentGroupInvalidExperimentInstance(task_name=name) from ex

    # combine(): Defined by Conductor at runtime
    # pylint: disable=undefined-variable
    combine(  # type: ignore
        name=name,
        deps=relative_experiment_identifiers,
    )
