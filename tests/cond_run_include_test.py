import pathlib

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES

# Scenarios where include() is used incorrectly.


def test_cond_include_badext(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])
    # Includes a file that does not have a ".cond" extension.
    res = cond.run("//errors/badext:main")
    assert res.returncode != 0


def test_cond_include_nonexistent_relative(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])
    # Includes a file using a relative path that does not exist.
    res = cond.run("//errors/nonexistent:main")
    assert res.returncode != 0


def test_cond_include_nonexistent_project_relative(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])
    # Includes a file using a project-relative path (e.g.
    # //path/to/include.cond) that does not exist.
    res = cond.run("//errors/nonexistent2:main")
    assert res.returncode != 0


def test_cond_include_external(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])
    # Includes a file that exists but is not in this project.
    res = cond.run("//errors/outside-project:main")
    assert res.returncode != 0


def test_cond_include_nested(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])
    # The included file also tries to include a file.
    res = cond.run("//errors/nested:main")
    assert res.returncode != 0


def test_cond_include_define_task(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])
    # The included file tries to define a task (this is not allowed).
    res = cond.run("//errors/defines-tasks:main")
    assert res.returncode != 0


# Scenarios where include() is used correctly.


def check_output_file(
    out_dir: pathlib.Path, expected_str: str, expected_value: int = (123 + 1337)
):
    # `expected_value` is the sum of `VALUE1` and `VALUE2`, which are defined in
    # the included `.cond` files.
    with open(out_dir / "out.txt", encoding="UTF-8") as file:
        contents = file.read().strip()
    parts = contents.split("-")
    assert len(parts) == 2
    assert parts[0] == expected_str
    assert int(parts[1]) == expected_value


def test_cond_include_exp_separate(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])

    res = cond.run("//sharing/exp1:exp1")
    assert res.returncode == 0
    exp1_out = cond.find_task_output_dir("//sharing/exp1:exp1", is_experiment=True)
    assert exp1_out is not None
    check_output_file(exp1_out, "exp1")

    res = cond.run("//sharing/exp2:exp2")
    assert res.returncode == 0
    exp2_out = cond.find_task_output_dir("//sharing/exp2:exp2", is_experiment=True)
    assert exp2_out is not None
    check_output_file(exp2_out, "exp2")


def test_cond_include_exp_combined(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["include"])

    # This should exercise the include caching codepath. Both dependencies of
    # `//sharing:combine` include the same files.
    res = cond.run("//sharing:both")
    assert res.returncode == 0

    # Sanity check.
    both_out = cond.find_task_output_dir("//sharing:both", is_experiment=False)
    assert both_out is not None

    exp1_out = cond.find_task_output_dir("//sharing/exp1:exp1", is_experiment=True)
    assert exp1_out is not None
    check_output_file(exp1_out, "exp1")

    exp2_out = cond.find_task_output_dir("//sharing/exp2:exp2", is_experiment=True)
    assert exp2_out is not None
    check_output_file(exp2_out, "exp2")
