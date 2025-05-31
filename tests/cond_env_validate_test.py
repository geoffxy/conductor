import pathlib
import pytest
import subprocess
from typing import Iterable, Any

from .conductor_runner import (
    ConductorRunner,
    FIXTURE_TEMPLATES,
)

from conductor.context import Context
from conductor.errors import (
    EnvConfigScriptFailed,
    EnvConfigInvalid,
    EnvExtraFileNotFound,
    EnvExtraFileNotInRepository,
)
from conductor.execution.operation_state import OperationState
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.transfer_repo import TransferRepo
from conductor.task_identifier import TaskIdentifier


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


def test_invalid_extra_file(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    result = cond.run("//mod6:abs_file")
    assert result.returncode != 0
    err_msg = result.stderr.decode("utf-8")
    assert "EnvExtraFilesNotRelative" in err_msg


def test_missing_extra_file(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    working_path = cond.project_root
    run_git_command(tmp_path, ["init"])

    ctx = Context(working_path)
    ident = TaskIdentifier.from_str("//mod7:no_file")
    ctx.task_index.load_transitive_closure(ident)

    op = TransferRepo(
        initial_state=OperationState.QUEUED,
        env_name="mod7_env_missing",
    )
    with pytest.raises(EnvExtraFileNotFound):
        # pylint: disable-next=protected-access
        op._validate_and_process_extra_files(ctx)


def test_extra_file_validation(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    working_path = cond.project_root
    run_git_command(tmp_path, ["init"])

    ctx = Context(working_path)
    ident = TaskIdentifier.from_str("//mod7:simple")
    ctx.task_index.load_transitive_closure(ident)

    op = TransferRepo(
        initial_state=OperationState.QUEUED,
        env_name="mod7_env_exists",
    )
    # pylint: disable-next=protected-access
    op._validate_and_process_extra_files(ctx)


def test_extra_file_outside(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    working_path = cond.project_root
    run_git_command(working_path, ["init"])  # N.B. Git repo is not in `tmp_path`

    # Create the file outside the repository.
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("This is an outside file.")

    ctx = Context(working_path)
    ident = TaskIdentifier.from_str("//mod7:file_outside")
    ctx.task_index.load_transitive_closure(ident)

    op = TransferRepo(
        initial_state=OperationState.QUEUED,
        env_name="mod7_env_file_outside",
    )
    with pytest.raises(EnvExtraFileNotInRepository):
        # pylint: disable-next=protected-access
        op._validate_and_process_extra_files(ctx)


def run_git_command(repo_root: pathlib.Path, args: Iterable[Any]):
    res = subprocess.run(
        ["git", *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        cwd=repo_root,
    )
    assert res.returncode == 0
