from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence
from conductor.utils.run_arguments import ArgumentValue
from conductor.utils.run_options import OptionValue
from conductor.errors import (
    ExperimentGroupDuplicateName,
    ExperimentGroupInvalidExperimentInstance,
)


class ExperimentInstance(NamedTuple):
    name: str
    args: List[ArgumentValue] = []
    options: Dict[str, OptionValue] = {}
    parallelizable: bool = False


def run_experiment_group(
    name: str,
    run: str,
    experiments: Iterable[ExperimentInstance],
    chain_experiments: bool = False,
    deps: Optional[Sequence[str]] = None,
) -> None:
    task_deps = deps if deps is not None else []
    relative_experiment_identifiers = []
    prev_experiment_identifier: Optional[str] = None

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

            # Add the previously-processed task as a dependency if
            # `chain_experiments` is set to `True`.
            experiment_deps = task_deps
            if chain_experiments and prev_experiment_identifier is not None:
                experiment_deps = [*task_deps, prev_experiment_identifier]

            # run_experiment(): Defined by Conductor at runtime
            # pylint: disable=undefined-variable
            run_experiment(  # type: ignore
                name=experiment.name,
                run=run,
                parallelizable=experiment.parallelizable,
                args=experiment.args,
                options=experiment.options,
                deps=experiment_deps,
            )
            experiment_identifier = ":" + experiment.name
            relative_experiment_identifiers.append(experiment_identifier)
            prev_experiment_identifier = experiment_identifier

    except TypeError as ex:
        raise ExperimentGroupInvalidExperimentInstance(task_name=name) from ex

    # combine(): Defined by Conductor at runtime
    # pylint: disable=undefined-variable
    combine(  # type: ignore
        name=name,
        deps=relative_experiment_identifiers,
    )
