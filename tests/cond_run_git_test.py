import pathlib
import shutil
import subprocess
from typing import Any, Iterable

from conductor.config import TASK_OUTPUT_DIR_SUFFIX
from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES


CHECK_FILE_PATH = pathlib.Path("copy" + TASK_OUTPUT_DIR_SUFFIX, "copied.txt")


def run_git_command(repo_root: pathlib.Path, args: Iterable[Any]):
    res = subprocess.run(
        ["git", *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        cwd=repo_root,
    )
    assert res.returncode == 0


def set_up_git_repository(tmp_path: pathlib.Path):
    # Set up the following commit history
    #
    # [master1] ---> [master2] ---> [brancha]
    #                    |
    #                    +--------> [branchb]

    def run(args: Iterable[Any]):
        run_git_command(tmp_path, args)

    run(["init"])
    shutil.move(tmp_path / "gen-master1.sh", tmp_path / "generate.sh")
    run(["add", "COND", "cond_config.toml", "copy.sh", "generate.sh"])
    run(["commit", "-m", "master1"])
    run(["checkout", "-b", "master1"])

    run(["checkout", "-b", "master2"])
    shutil.move(tmp_path / "gen-master2.sh", tmp_path / "generate.sh")
    run(["add", "generate.sh"])
    run(["commit", "-m", "master2"])

    run(["checkout", "-b", "brancha"])
    shutil.move(tmp_path / "gen-brancha.sh", tmp_path / "generate.sh")
    run(["add", "generate.sh"])
    run(["commit", "-m", "brancha"])

    run(["checkout", "master2"])
    run(["checkout", "-b", "branchb"])
    shutil.move(tmp_path / "gen-branchb.sh", tmp_path / "generate.sh")
    run(["add", "generate.sh"])
    run(["commit", "-m", "branchb"])


def load_file_contents(file_path: pathlib.Path) -> str:
    with open(file_path, encoding="UTF-8") as f:
        return f.read().strip()


def test_use_relevant(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    run_git_command(repo_path, ["checkout", "master1"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    # Should use `master1`'s cached copy.
    run_git_command(repo_path, ["checkout", "brancha"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    # Should use the latest script at `brancha`.
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"

    # Should use `master1`'s cached copy because `brancha` is not an ancestor of
    # `branchb`.
    run_git_command(repo_path, ["checkout", "branchb"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    # Should now use the latest script at `branchb`.
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "branchb"

    # Should use the cached result from `master1`
    run_git_command(repo_path, ["checkout", "master2"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"
