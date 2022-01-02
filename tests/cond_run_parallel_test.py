import pathlib
import shutil
import subprocess
from typing import Any, Iterable

from conductor.config import TASK_OUTPUT_DIR_SUFFIX, STDOUT_LOG_FILE, STDERR_LOG_FILE
from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES


def extract_logged_slot(result_path: pathlib.Path) -> int:
    slots_file = result_path / "slot.txt"
    assert slots_file.exists()
    with open(slots_file, encoding="UTF-8") as f:
        return int(f.read().strip())


def test_invalid_jobs(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    # When specified, the number of jobs has to be at least 1.
    result = cond.run("//parallel:three", jobs=0)
    assert result.returncode != 0
    result = cond.run("//parallel:three", jobs=-10)
    assert result.returncode != 0


def test_run_parallel(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//parallel:three", jobs=3)
    assert result.returncode == 0

    outputs = cond.output_path / "parallel" / ("three" + TASK_OUTPUT_DIR_SUFFIX)
    paths = [
        (outputs / "three-0"),
        (outputs / "three-1"),
        (outputs / "three-2"),
    ]
    assert all(map(lambda p: p.is_dir(), paths))

    seen_slots = set()
    for idx, out_dir in enumerate(paths):
        slot = extract_logged_slot(out_dir)
        seen_slots.add(slot)

        arg_file = out_dir / "arg1.txt"
        assert arg_file.exists()
        with open(arg_file, encoding="UTF-8") as f:
            arg = int(f.read().strip())
        assert arg == idx

        # Even if running in parallel, we should still log the task's output on
        # stdout and stderr.
        stdout_file = out_dir / STDOUT_LOG_FILE
        assert stdout_file.exists()
        with open(stdout_file, encoding="UTF-8") as f:
            parts = f.read().strip().split(" ")
        assert parts[0] == "stdout"
        assert int(parts[1]) == slot

        stderr_file = out_dir / STDERR_LOG_FILE
        assert stderr_file.exists()
        with open(stderr_file, encoding="UTF-8") as f:
            parts = f.read().strip().split(" ")
        assert parts[0] == "stderr"
        assert int(parts[1]) == slot

    # We ran with 3 jobs, so the three tasks should have been allowed to run in
    # parallel.
    assert len(seen_slots) == 3


def test_run_parallel_fewer_slots(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//parallel:three", jobs=2)
    assert result.returncode == 0

    outputs = cond.output_path / "parallel" / ("three" + TASK_OUTPUT_DIR_SUFFIX)
    paths = [
        (outputs / "three-0"),
        (outputs / "three-1"),
        (outputs / "three-2"),
    ]
    assert all(map(lambda p: p.is_dir(), paths))

    seen_slots = set()
    for idx, out_dir in enumerate(paths):
        slot = extract_logged_slot(out_dir)
        seen_slots.add(slot)

        arg_file = out_dir / "arg1.txt"
        assert arg_file.exists()
        with open(arg_file, encoding="UTF-8") as f:
            arg = int(f.read().strip())
        assert arg == idx

    # At most two tasks run in parallel.
    assert len(seen_slots) == 2


def test_run_parallel_but_sequential(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    # This task is parallelizable, but we restrict Conductor to running no more
    # than a single task at a time. There should be no slot number passed to the
    # task (to indicate sequential execution).
    result = cond.run("//parallel:three", jobs=1)
    assert result.returncode == 0

    outputs = cond.output_path / "parallel" / ("three" + TASK_OUTPUT_DIR_SUFFIX)
    paths = [
        (outputs / "three-0"),
        (outputs / "three-1"),
        (outputs / "three-2"),
    ]
    assert all(map(lambda p: p.is_dir(), paths))

    # No slot printed.
    for out_dir in paths:
        with open(out_dir / "slot.txt") as f:
            assert f.read().strip() == ""


def test_run_sequential_multiple_jobs(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    # This task is NOT parallelizable, but we set jobs to be greater than 1.
    # Regardless, there should be no slot number passed to the task (to indicate
    # sequential execution).
    result = cond.run("//parallel:three_seq", jobs=5)
    assert result.returncode == 0

    outputs = cond.output_path / "parallel" / ("three_seq" + TASK_OUTPUT_DIR_SUFFIX)
    paths = [
        (outputs / "three_seq-0"),
        (outputs / "three_seq-1"),
        (outputs / "three_seq-2"),
    ]
    assert all(map(lambda p: p.is_dir(), paths))

    # No slot printed.
    for out_dir in paths:
        with open(out_dir / "slot.txt") as f:
            assert f.read().strip() == ""
