import pathlib
from .conductor_runner import ConductorRunner, EXAMPLE_TEMPLATES


def test_cond_run(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world")
    assert result.returncode == 0
    assert cond.output_path.exists()

    def count_task_outputs():
        num_dirs = 0
        for file in cond.output_path.iterdir():
            if file.is_dir():
                assert file.name.startswith("hello_world.task")
                num_dirs += 1
        return num_dirs

    assert count_task_outputs() == 1

    # Should use cached result
    result = cond.run("//:hello_world")
    assert result.returncode == 0
    assert count_task_outputs() == 1

    # Should create a new task output
    result = cond.run("//:hello_world", again=True)
    assert result.returncode == 0
    assert count_task_outputs() == 2


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
