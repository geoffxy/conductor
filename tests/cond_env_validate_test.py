import pathlib

from .conductor_runner import (
    ConductorRunner,
    FIXTURE_TEMPLATES,
)


def test_missing_env(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    result = cond.run("//mod2:test3")
    assert result.returncode != 0
    err_msg = result.stderr.decode("utf-8")
    assert "EnvNotFound" in err_msg


def test_dup_env(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    result = cond.run("//mod3:test5")
    assert result.returncode != 0
    err_msg = result.stderr.decode("utf-8")
    assert "DuplicateEnvName" in err_msg


def test_not_env(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    result = cond.run("//mod4:test6")
    assert result.returncode != 0
    err_msg = result.stderr.decode("utf-8")
    assert "EnvNotEnv" in err_msg
