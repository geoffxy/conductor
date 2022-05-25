import pathlib
from typing import List

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES


def test_gc_failed_tasks(tmp_path: pathlib.Path):
    # This test is based off of `test_cond_run_multiple_failures()` in
    # `cond_run_test.py`.

    # The task has multiple dependencies that may fail. Conductor should, by
    # default, attempt to run all the tasks that can be executed (i.e., it
    # should not stop at the first failure).
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # Expected to fail overall.
    result = cond.run("//multiple:sweep")
    assert result.returncode != 0

    # Check for expected output files.

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

    # Run `cond gc` to delete the failed tasks' output directories.
    result = cond.gc()
    assert result.returncode == 0

    # Check that the failed tasks' output directories were actually removed.
    for idx in range(6):
        sweep_idx = cond.find_task_output_dir(
            "//multiple:sweep-{}".format(idx), is_experiment=True
        )
        if idx % 2 == 0:
            # Executed but failed.
            assert sweep_idx is None
        else:
            # Executed and succeeded.
            assert sweep_idx is not None
            assert (sweep_idx / "date.txt").exists()


def test_gc_dry_run(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # Expected to fail overall.
    result = cond.run("//multiple:sweep")
    assert result.returncode != 0

    # Check for expected output files.

    # The top level `run_experiment_group()` task is technically not a Conductor experiment task.
    sweep_out = cond.find_task_output_dir("//multiple:sweep", is_experiment=False)
    assert sweep_out is None

    # Succeeded/failed sweep tasks
    expected_to_remove: List[pathlib.Path] = []
    for idx in range(6):
        sweep_idx = cond.find_task_output_dir(
            "//multiple:sweep-{}".format(idx), is_experiment=True
        )
        assert sweep_idx is not None

        if idx % 2 == 0:
            # Executed but failed.
            assert not (sweep_idx / "date.txt").exists()
            expected_to_remove.append(sweep_idx)
        else:
            # Executed and succeeded.
            assert (sweep_idx / "date.txt").exists()

    # Run `cond gc --dry-run`. We should only print the directories that would
    # be deleted.
    result = cond.gc(dry_run=True)
    assert result.returncode == 0

    # Check that the failed tasks' output directories were *not* actually removed.
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

    # Check that all the directories that we expect to be removed are mentioned
    # in the output.
    out_as_str = result.stdout.decode(encoding="UTF-8")
    for to_remove in expected_to_remove:
        assert to_remove.name in out_as_str


def test_gc_verbose(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["partial-success"])

    # Expected to fail overall.
    result = cond.run("//multiple:sweep")
    assert result.returncode != 0

    # Check for expected output files.

    # The top level `run_experiment_group()` task is technically not a Conductor experiment task.
    sweep_out = cond.find_task_output_dir("//multiple:sweep", is_experiment=False)
    assert sweep_out is None

    # Succeeded/failed sweep tasks
    expected_to_remove: List[pathlib.Path] = []
    for idx in range(6):
        sweep_idx = cond.find_task_output_dir(
            "//multiple:sweep-{}".format(idx), is_experiment=True
        )
        assert sweep_idx is not None

        if idx % 2 == 0:
            # Executed but failed.
            assert not (sweep_idx / "date.txt").exists()
            expected_to_remove.append(sweep_idx)
        else:
            # Executed and succeeded.
            assert (sweep_idx / "date.txt").exists()

    # Run `cond gc --verbose`. We should print the directories that are being
    # deleted.
    result = cond.gc(verbose=True)
    assert result.returncode == 0

    # Check that the failed tasks' output directories were removed.
    for idx in range(6):
        sweep_idx = cond.find_task_output_dir(
            "//multiple:sweep-{}".format(idx), is_experiment=True
        )

        if idx % 2 == 0:
            # Executed but failed.
            assert sweep_idx is None
        else:
            # Executed and succeeded.
            assert sweep_idx is not None
            assert (sweep_idx / "date.txt").exists()

    # Check that all the directories that we expect to be removed are mentioned
    # in the output.
    out_as_str = result.stdout.decode(encoding="UTF-8")
    for to_remove in expected_to_remove:
        assert to_remove.name in out_as_str
