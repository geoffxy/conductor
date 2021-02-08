import pathlib
from conductor.config import TASK_OUTPUT_DIR_SUFFIX
from .conductor_runner import (
    ConductorRunner,
    FIXTURE_TEMPLATES,
)


def test_run_experiment_group(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//sweep:threads")
    assert result.returncode == 0
    assert cond.output_path.is_dir()

    combined_dir = pathlib.Path(
        cond.output_path, "sweep", ("threads" + TASK_OUTPUT_DIR_SUFFIX)
    )
    assert combined_dir.is_dir()

    expected_tasks = ["threads-{}".format(threads) for threads in range(1, 5)]

    # Ensure combined task dirs all exist and are non-empty.
    combined_dir_names = [path.name for path in combined_dir.iterdir()]
    for task_name in expected_tasks:
        assert task_name in combined_dir_names
        assert any(True for _ in (combined_dir / task_name).iterdir())

    # Ensure individual experiment dirs also exist.
    sweep_output = combined_dir.parent
    assert sweep_output.is_dir()
    sweep_output_count = len(list(sweep_output.iterdir()))

    # 4 experiment instances plus the combined output dir.
    assert sweep_output_count == 5


def test_run_experiment_group_invalid_duplicate(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//invalid-group-duplicate:test")
    assert result.returncode != 0


def test_run_experiment_group_invalid_type(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//invalid-group-type:test")
    assert result.returncode != 0
