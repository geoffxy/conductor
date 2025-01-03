import csv
import json
import os
import pathlib
import sys

import pytest

from conductor.config import (
    TASK_OUTPUT_DIR_SUFFIX,
    STDOUT_LOG_FILE,
    STDERR_LOG_FILE,
    EXP_OPTION_JSON_FILE_NAME,
)
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
    with open(graph_csv, "r", encoding="UTF-8") as file:
        graph1 = list(csv.reader(file))

    # Conductor should use the cached benchmark result. Therefore the generated
    # graph.csv files should remain identical.
    result = cond.run("//figures:graph")
    assert result.returncode == 0
    assert count_task_outputs(experiment_out) == 2
    assert count_task_outputs(figures_out) == 1

    assert graph_csv.exists()
    with open(graph_csv, "r", encoding="UTF-8") as file:
        graph2 = list(csv.reader(file))

    assert graph1 == graph2

    # Force benchmark to run again. We should get a new benchmark output.
    result = cond.run("//figures:graph", again=True)
    assert result.returncode == 0
    assert count_task_outputs(experiment_out) == 3
    assert count_task_outputs(figures_out) == 1


def test_cond_run_combine(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["combine-test"])

    def run_assertions():
        result = cond.run("//:all")
        assert result.returncode == 0
        assert cond.output_path.exists()

        combine_task_output_dir = cond.output_path / ("all" + TASK_OUTPUT_DIR_SUFFIX)
        assert combine_task_output_dir.exists()

        task_dirs = [file.name for file in combine_task_output_dir.iterdir()]
        assert len(task_dirs) == 2
        assert "echo1" in task_dirs
        assert "echo2" in task_dirs

        file1 = combine_task_output_dir / "echo1" / "file1.txt"
        assert file1.is_file()
        assert (combine_task_output_dir / "echo2" / "file2.txt").is_file()

    run_assertions()
    # Should be able to re-run the task without any problems
    run_assertions()


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

    with open(out_file, encoding="UTF-8") as file:
        values = [line.rstrip(os.linesep) for line in file]
    assert values == ["1", "2", "3"]
    out_file.unlink()

    result = cond.run("//:order213")
    assert result.returncode == 0
    assert out_file.exists()

    with open(out_file, encoding="UTF-8") as file:
        values = [line.rstrip(os.linesep) for line in file]
    assert values == ["2", "1", "3"]


def test_cond_run_duplicate_deps(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["combine-test"])
    result = cond.run("//duplicate-deps:test")
    assert result.returncode != 0


def test_cond_run_combine_duplicates(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["combine-test"])
    result = cond.run("//duplicate-names:test")
    assert result.returncode != 0


def test_cond_run_check_no_run(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world", check=True)
    assert result.returncode == 0
    assert cond.output_path.exists()
    # Conductor should not actually run the task when --check is set.
    assert count_task_outputs(cond.output_path) == 0


def test_cond_run_check_error(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["combine-test"])
    result = cond.run("//duplicate-names:test", check=True)
    assert result.returncode != 0


def test_cond_run_record_output(tmp_path: pathlib.Path):
    # This test tests Conductor's ability to record the stdout/stderr output of
    # a `run_experiment()` task.

    cond = ConductorRunner.from_template(
        tmp_path, FIXTURE_TEMPLATES["output-recording"]
    )
    result = cond.run("//:test")
    assert result.returncode == 0
    assert cond.output_path.is_dir()

    task_output_dir = None
    for file in cond.output_path.iterdir():
        if file.name.startswith("test" + TASK_OUTPUT_DIR_SUFFIX):
            task_output_dir = file
            break
    assert task_output_dir is not None

    stdout_file = task_output_dir / STDOUT_LOG_FILE
    stderr_file = task_output_dir / STDERR_LOG_FILE
    assert stdout_file.is_file()
    assert stderr_file.is_file()

    stdout_contents = [
        line.rstrip() for line in open(stdout_file, "r", encoding="UTF-8")
    ]
    assert len(stdout_contents) == 1
    assert stdout_contents[0] == "!!stdout!!"
    # Ensures that the task's stdout output is still written out to stdout
    assert stdout_contents[0] in result.stdout.decode(sys.stdout.encoding)

    stderr_contents = [
        line.rstrip() for line in open(stderr_file, "r", encoding="UTF-8")
    ]
    assert len(stderr_contents) == 1
    assert stderr_contents[0] == "!!stderr!!"
    # Ensures that the task's stderr output is still written out to stderr
    assert stderr_contents[0] in result.stderr.decode(sys.stderr.encoding)


def test_cond_run_experiment_options(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//options:test")
    assert result.returncode == 0
    assert cond.output_path.is_dir()

    options_dir = cond.output_path / "options"
    assert options_dir.is_dir()

    # Locate the task output directory
    task_output_dir = None
    for file in options_dir.iterdir():
        if file.name.startswith("test" + TASK_OUTPUT_DIR_SUFFIX):
            task_output_dir = file
            break
    assert task_output_dir is not None

    # Read the outputted file and make sure the arguments were visible to the
    # underlying bash script.
    seen_options = [
        line.rstrip()
        for line in open(task_output_dir / "all_options.txt", "r", encoding="UTF-8")
    ]
    assert len(seen_options) == 4
    assert "--key=value" in seen_options
    assert "--threads=2" in seen_options
    assert "--retry=true" in seen_options
    assert "--epsilon=0.05" in seen_options

    serialized_json_file = task_output_dir / EXP_OPTION_JSON_FILE_NAME
    assert serialized_json_file.is_file()
    with open(serialized_json_file, "r", encoding="UTF-8") as json_file:
        json_opts = json.load(json_file)

    # Make sure the options serialization worked correctly.
    assert len(json_opts) == len(seen_options)
    assert json_opts["key"] == "value"
    assert json_opts["threads"] == 2
    assert json_opts["retry"] == True
    assert json_opts["epsilon"] == pytest.approx(0.05)


def test_cond_run_invalid_experiment_options(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    # These tasks have invalid options.
    result = cond.run("//invalid-options:test-invalid-numeric")
    assert result.returncode != 0
    result = cond.run("//invalid-options:test-invalid-complex")
    assert result.returncode != 0


def test_cond_run_command_options(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//options:test_command")
    assert result.returncode == 0
    assert cond.output_path.is_dir()

    options_dir = cond.output_path / "options"
    assert options_dir.is_dir()

    # Locate the task output directory
    task_output_dir = None
    for file in options_dir.iterdir():
        if file.name.startswith("test_command" + TASK_OUTPUT_DIR_SUFFIX):
            task_output_dir = file
            break
    assert task_output_dir is not None

    # Read the outputted file and make sure the arguments were visible to the
    # underlying bash script.
    seen_options = [
        line.rstrip()
        for line in open(task_output_dir / "all_options.txt", "r", encoding="UTF-8")
    ]
    assert len(seen_options) == 4
    assert "--key=value" in seen_options
    assert "--threads=2" in seen_options
    assert "--retry=true" in seen_options
    assert "--epsilon=0.05" in seen_options


def test_cond_run_invalid_command_options(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    # These tasks have invalid options.
    result = cond.run("//invalid-options:test-invalid-numeric-command")
    assert result.returncode != 0
    result = cond.run("//invalid-options:test-invalid-complex-command")
    assert result.returncode != 0


def test_cond_run_partial_success(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])
    # Expected to fail.
    result = cond.run("//:noop")
    assert result.returncode != 0
    # We should have run the //:datetime task.
    assert "//:datetime" in result.stdout.decode()

    # Even though the previous task failed, its dependency should have
    # succeeded. Running the dependent task should be a no-op (the results
    # should be cached).
    result = cond.run("//:datetime")
    assert result.returncode == 0
    assert "cached" in result.stdout.decode()


def test_cond_run_multiple_failures(tmp_path: pathlib.Path):
    # The task has multiple dependencies that may fail. Conductor should, by
    # default, attempt to run all the tasks that can be executed (i.e., it
    # should not stop at the first failure).
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # Expected to fail overall.
    result = cond.run("//multiple:root")
    assert result.returncode != 0

    # Check for expected output files.

    # Skipped tasks
    root_out = cond.find_task_output_dir("//multiple:root", is_experiment=True)
    assert root_out is None
    should_skip_out = cond.find_task_output_dir(
        "//multiple:should_skip", is_experiment=True
    )
    assert should_skip_out is None
    # The top level `run_experiment_group()` task is technically not a Conductor experiment task.
    sweep_out = cond.find_task_output_dir("//multiple:sweep", is_experiment=False)
    assert sweep_out is None

    # Succeeded/failed sweep tasks
    for idx in range(6):
        sweep_idx = cond.find_task_output_dir(
            "//multiple:sweep-{}".format(idx), is_experiment=True
        )
        assert sweep_idx is not None

        if idx % 2 == 0:
            # Executed but failed.
            assert not (sweep_idx / "date.txt").exists()
        else:
            # Executed and succeeded.
            assert (sweep_idx / "date.txt").exists()

    # `//multiple:should_run` should have executed and succeeded
    should_run_out = cond.find_task_output_dir(
        "//multiple:should_run", is_experiment=False
    )
    assert should_run_out is not None
    assert (should_run_out / "date.txt").exists()


def test_cond_run_multiple_failures_stop_early(tmp_path: pathlib.Path):
    # The task has multiple dependencies that may fail. If requested, Conductor
    # should stop running the task when it encounters the first failure.
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # Expected to fail overall.
    result = cond.run("//multiple:root", stop_early=True)
    assert result.returncode != 0

    # Check for expected output files.
    # `:sweep-1` should run first. Then `:sweep-0` will run, which will fail. No
    # other tasks should be attempted.

    # Runs and succeeds.
    sweep1 = cond.find_task_output_dir("//multiple:sweep-1", is_experiment=True)
    assert sweep1 is not None
    assert (sweep1 / "date.txt").exists()

    # `//multiple:should_run` should not have been attempted (Conductor now
    # executes tasks breadth first).
    should_run_out = cond.find_task_output_dir(
        "//multiple:should_run", is_experiment=False
    )
    assert should_run_out is None

    # Runs but fails.
    sweep0 = cond.find_task_output_dir("//multiple:sweep-0", is_experiment=True)
    assert sweep0 is not None
    assert not (sweep0 / "date.txt").exists()

    # All other tasks should not have even been attempted.
    for idx in range(2, 6):
        sweep_idx = cond.find_task_output_dir(
            "//multiple:sweep-{}".format(idx), is_experiment=True
        )
        assert sweep_idx is None

    root_out = cond.find_task_output_dir("//multiple:root", is_experiment=True)
    assert root_out is None
    should_skip_out = cond.find_task_output_dir(
        "//multiple:should_skip", is_experiment=True
    )
    assert should_skip_out is None
    # The top level `run_experiment_group()` task is technically not a Conductor experiment task.
    sweep_out = cond.find_task_output_dir("//multiple:sweep", is_experiment=False)
    assert sweep_out is None


def test_cond_run_chained(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    # The task checks that chaining occurs.
    result = cond.run("//sweep:chained-test", jobs=5)
    assert result.returncode == 0
