import csv
import pathlib
import os

from conductor.config import TASK_OUTPUT_DIR_SUFFIX
from .conductor_runner import (
    ConductorRunner,
    count_task_outputs,
    EXAMPLE_TEMPLATES,
    FIXTURE_TEMPLATES,
)


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


def test_cond_run_combine(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["combine-test"])
    result = cond.run("//:all")
    assert result.returncode == 0
    assert cond.output_path.exists()

    combine_task_output_dir = cond.output_path / ("all" + TASK_OUTPUT_DIR_SUFFIX)
    assert combine_task_output_dir.exists()

    files = [file.name for file in combine_task_output_dir.iterdir()]
    assert len(files) == 2
    assert "file1.txt" in files
    assert "file2.txt" in files


def test_cond_run_ordering(tmp_path: pathlib.Path):
    # This test ensures we run a task's directly dependent tasks (i.e., first
    # level dependencies) in the order they are listed in the task's
    # definition. This behavior is just for the user's convenience. Conductor
    # only guarantees that a task's dependents have executed before the task
    # itself is executed.

    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["ordering-test"])
    result = cond.run("//:order123")
    assert result.returncode == 0
    assert cond.output_path.exists()

    out_file = cond.output_path / "out.txt"
    assert out_file.exists()

    with open(out_file) as file:
        values = [line.rstrip(os.linesep) for line in file]
    assert values == ["1", "2", "3"]
    out_file.unlink()

    result = cond.run("//:order213")
    assert result.returncode == 0
    assert out_file.exists()

    with open(out_file) as file:
        values = [line.rstrip(os.linesep) for line in file]
    assert values == ["2", "1", "3"]


def test_cond_run_duplicate_deps(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["combine-test"])
    result = cond.run("//duplicate-deps:test")
    assert result.returncode != 0
