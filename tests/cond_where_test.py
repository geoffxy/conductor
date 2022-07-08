import pathlib

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES
from conductor.config import TASK_OUTPUT_DIR_SUFFIX


def extract_output_path(out: bytes):
    return out.decode(encoding="UTF-8").strip()


def test_cond_where_nonexistent(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # The task has not run yet.
    res = cond.where("//multiple:should_run")
    assert res.returncode != 0

    # The task has not run yet.
    res = cond.where("//multiple:sweep-0")
    assert res.returncode != 0


def test_cond_where_nonexistent_ok(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # This is a run_command() task.
    res = cond.where("//multiple:should_run", non_existent_ok=True)
    assert res.returncode == 0
    path = extract_output_path(res.stdout)
    expected_location = (
        cond.output_path / "multiple" / "should_run{}".format(TASK_OUTPUT_DIR_SUFFIX)
    )
    assert path == str(expected_location)
    assert not expected_location.exists()

    # This is a run_experiment() task. A version must exist for cond where to
    # print a path.
    res = cond.where("//multiple:sweep-0", non_existent_ok=True)
    assert res.returncode != 0


def test_cond_where(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # This is expected to partially fail.
    res = cond.run("//multiple:sweep")
    assert res.returncode != 0

    res = cond.run("//multiple:should_run")
    assert res.returncode == 0

    # Absolute path.
    res = cond.where("//multiple:should_run")
    assert res.returncode == 0
    expected_location = (
        cond.output_path / "multiple" / "should_run{}".format(TASK_OUTPUT_DIR_SUFFIX)
    )
    assert extract_output_path(res.stdout) == str(expected_location)

    # Relative to project root.
    res = cond.where("//multiple:should_run", project=True)
    assert res.returncode == 0
    expected_rel_location = expected_location.relative_to(cond.project_root)
    assert extract_output_path(res.stdout) == str(expected_rel_location)

    # This task failed.
    res = cond.where("//multiple:sweep-0")
    assert res.returncode != 0

    # Experiment task.
    res = cond.where("//multiple:sweep-1")
    assert res.returncode == 0
    expected_exp_loc = cond.find_task_output_dir(
        "//multiple:sweep-1", is_experiment=True
    )
    assert expected_exp_loc is not None
    assert extract_output_path(res.stdout) == str(expected_exp_loc)

    # Relative to project root.
    res = cond.where("//multiple:sweep-1", project=True)
    assert res.returncode == 0
    expected_rel_exp_loc = expected_exp_loc.relative_to(cond.project_root)
    assert expected_rel_exp_loc is not None
    assert extract_output_path(res.stdout) == str(expected_rel_exp_loc)
