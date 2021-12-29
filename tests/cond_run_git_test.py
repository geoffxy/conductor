import pathlib
import shutil
import subprocess
from typing import Any, Iterable

from conductor.config import TASK_OUTPUT_DIR_SUFFIX, CONFIG_FILE_NAME
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
    shutil.move(str(tmp_path / "gen-master1.sh"), str(tmp_path / "generate.sh"))
    run(["add", "COND", "cond_config.toml", "copy.sh", "generate.sh"])
    run(["commit", "-m", "master1"])
    run(["checkout", "-b", "master1"])

    run(["checkout", "-b", "master2"])
    shutil.move(str(tmp_path / "gen-master2.sh"), str(tmp_path / "generate.sh"))
    run(["add", "generate.sh"])
    run(["commit", "-m", "master2"])

    run(["checkout", "-b", "brancha"])
    shutil.move(str(tmp_path / "gen-brancha.sh"), str(tmp_path / "generate.sh"))
    run(["add", "generate.sh"])
    run(["commit", "-m", "brancha"])

    run(["checkout", "master2"])
    run(["checkout", "-b", "branchb"])
    shutil.move(str(tmp_path / "gen-branchb.sh"), str(tmp_path / "generate.sh"))
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


def test_bare_repo(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"
    shutil.move(str(repo_path / "gen-master1.sh"), str(repo_path / "generate.sh"))
    run_git_command(repo_path, ["init"])

    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    shutil.move(str(repo_path / "gen-master2.sh"), str(repo_path / "generate.sh"))

    # Should use old cached copy.
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    # Should re-run and select the latest version.
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master2"


def test_multiple_ancestors_most_recent(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    run_git_command(repo_path, ["checkout", "branchb"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "branchb"

    run_git_command(repo_path, ["checkout", "brancha"])
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"

    # Create a merge commit (auto resolve conflicts).
    run_git_command(
        repo_path,
        [
            "merge",
            "branchb",
            "--strategy-option",
            "theirs",
            "--no-ff",
            "-m",
            "Test merge.",
        ],
    )

    # Should use the most recent cached copy.
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"

    # Re-running produces "branchb" because the merge strategy prefers the base
    # branch.
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "branchb"


def test_existing_but_not_ancestor(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    run_git_command(repo_path, ["checkout", "brancha"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"

    # The `brancha` result is more recent, but because the current commit is not
    # an ancestor of `brancha` we need to re-run the task.
    run_git_command(repo_path, ["checkout", "master1"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"


def test_context_supercedes_recency(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    run_git_command(repo_path, ["checkout", "master1"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    run_git_command(repo_path, ["checkout", "brancha"])
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"

    # The `brancha` result is more recent, but is not an ancestor of the current
    # commit. So we should use the `master1` result.
    run_git_command(repo_path, ["checkout", "master2"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"


def test_all_no_commit(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"

    shutil.move(str(repo_path / "gen-master1.sh"), str(repo_path / "generate.sh"))
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    shutil.move(str(repo_path / "gen-master2.sh"), str(repo_path / "generate.sh"))
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master2"

    run_git_command(repo_path, ["init"])
    run_git_command(
        repo_path, ["add", "COND", "cond_config.toml", "copy.sh", "generate.sh"]
    )
    run_git_command(repo_path, ["commit", "-m", "New repository."])

    # All prior versions have null commits (new repository). So we should be
    # using the latest archived version.
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master2"


def test_null_commit_and_no_ancestor(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"

    # This version is not tied to a particular commit (no repository).
    shutil.copy2(repo_path / "gen-master1.sh", repo_path / "generate.sh")
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    set_up_git_repository(repo_path)

    # Should use the cached (latest) version.
    run_git_command(repo_path, ["checkout", "brancha"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    # Force re-run produces a `brancha` result.
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"

    # Neither existing version is "compatible" (one is not an ancestor, the
    # other has no commit information). So Conductor chooses to re-run to be
    # conservative.
    run_git_command(repo_path, ["checkout", "branchb"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "branchb"


def test_disabled_git_use_recency(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-context"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    run_git_command(repo_path, ["checkout", "master1"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "master1"

    run_git_command(repo_path, ["checkout", "brancha"])
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"

    # Disable git integration.
    with open(repo_path / CONFIG_FILE_NAME, "w", encoding="UTF-8") as file:
        file.write("disable_git = true\n")

    # If git integration was enabled, this should return a `master1` result.
    # Instead Conductor will rely on recency to select a cached version.
    run_git_command(repo_path, ["checkout", "branchb"])
    res = cond.run("//:copy")
    assert res.returncode == 0
    assert load_file_contents(cond.output_path / CHECK_FILE_PATH) == "brancha"
