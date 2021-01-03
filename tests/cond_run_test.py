import csv
import pathlib
from .conductor_runner import ConductorRunner, count_task_outputs, EXAMPLE_TEMPLATES


def test_cond_run(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world")
    assert result.returncode == 0
    assert cond.output_path.exists()
    assert count_task_outputs(cond.output_path) == 1

    # Should use cached result
    result = cond.run("//:hello_world")
    assert result.returncode == 0
    assert count_task_outputs(cond.output_path) == 1

    # Should create a new task output
    result = cond.run("//:hello_world", again=True)
    assert result.returncode == 0
    assert count_task_outputs(cond.output_path) == 2


def test_cond_run_invalid(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//hello_world")
    assert result.returncode != 0

    result = cond.run("hello_world")
    assert result.returncode != 0

    result = cond.run("//:nonexistent")
    assert result.returncode != 0

    result = cond.run("//")
    assert result.returncode != 0

    result = cond.run("/hello")
    assert result.returncode != 0


def test_cond_run_deps(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["dependencies"])
    result = cond.run("//figures:graph")
    assert result.returncode == 0
    assert cond.output_path.exists()

    experiment_out = cond.output_path / "experiments"
    assert experiment_out.exists()
    assert count_task_outputs(experiment_out) == 2

    figures_out = cond.output_path / "figures"
    assert figures_out.exists()
    assert count_task_outputs(figures_out) == 1

    graph_csv = pathlib.Path(figures_out, "graph.task", "graph.csv")
    assert graph_csv.exists()
    with open(graph_csv, "r") as file:
        graph1 = list(csv.reader(file))

    # Conductor should use the cached benchmark result. Therefore the generated
    # graph.csv files should remain identical.
    result = cond.run("//figures:graph")
    assert result.returncode == 0
    assert count_task_outputs(experiment_out) == 2
    assert count_task_outputs(figures_out) == 1

    assert graph_csv.exists()
    with open(graph_csv, "r") as file:
        graph2 = list(csv.reader(file))

    assert graph1 == graph2

    # Force benchmark to run again. We should get a new benchmark output.
    result = cond.run("//figures:graph", again=True)
    assert result.returncode == 0
    assert count_task_outputs(experiment_out) == 3
    assert count_task_outputs(figures_out) == 1
