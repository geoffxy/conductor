from typing import Dict, Iterable, NamedTuple, Optional, Sequence
from conductor.utils.experiment_options import OptionValue


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

    for experiment in experiments:
        # pylint: disable=undefined-variable
        run_experiment(  # type: ignore
            name=experiment.name,
            run=run,
            options=experiment.options,
            deps=task_deps,
        )
        relative_experiment_identifiers.append(":" + experiment.name)

    # pylint: disable=undefined-variable
    combine(  # type: ignore
        name=name,
        deps=relative_experiment_identifiers,
    )
