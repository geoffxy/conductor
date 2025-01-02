import pathlib
import pytest

from .conductor_runner import (
    ConductorRunner,
    FIXTURE_TEMPLATES,
)

from conductor.errors import EnvConfigScriptFailed, EnvConfigInvalid
from conductor.execution.operation_state import OperationState
from conductor.execution.ops.start_remote_env import StartRemoteEnv


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


def test_invalid_config_scripts(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    working_path = cond.project_root / "mod5"

    # Non-existent script
    op0 = StartRemoteEnv(
        initial_state=OperationState.QUEUED,
        env_name="test",
        start_runnable=None,
        working_path=working_path,
        connect_config_runnable="./cfg0.sh",
    )
    with pytest.raises(EnvConfigScriptFailed):
        # pylint: disable-next=protected-access
        op0._get_raw_connect_config()

    # Invalid toml format
    op1 = StartRemoteEnv(
        initial_state=OperationState.QUEUED,
        env_name="test",
        start_runnable=None,
        working_path=working_path,
        connect_config_runnable="./cfg1.sh",
    )
    with pytest.raises(EnvConfigInvalid):
        # pylint: disable-next=protected-access
        op1._get_raw_connect_config()

    # Missing key, but valid format
    op2 = StartRemoteEnv(
        initial_state=OperationState.QUEUED,
        env_name="test",
        start_runnable=None,
        working_path=working_path,
        connect_config_runnable="./cfg2.sh",
    )
    with pytest.raises(EnvConfigInvalid):
        # pylint: disable-next=protected-access
        op2._get_raw_connect_config()


def test_valid_config_script(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    working_path = cond.project_root / "mod5"

    op = StartRemoteEnv(
        initial_state=OperationState.QUEUED,
        env_name="test",
        start_runnable=None,
        working_path=working_path,
        connect_config_runnable="./cfg3.sh",
    )
    # pylint: disable-next=protected-access
    config = op._get_raw_connect_config()
    assert config["host"] == "localhost"
    assert config["user"] == "geoffxy"
