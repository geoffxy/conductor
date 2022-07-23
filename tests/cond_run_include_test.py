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
