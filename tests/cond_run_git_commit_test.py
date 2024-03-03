import pathlib
import subprocess
from typing import Any, Iterable, Optional

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
    # Initializes the git repository.
    def run(args: Iterable[Any]):
        run_git_command(tmp_path, args)

    run(["init", "--initial-branch", "master"])
    run(["add", "COND", "cond_config.toml", "copy.py", "generate.sh"])
    run(["commit", "-m", "First commit."])


def load_file_contents(file_path: pathlib.Path) -> str:
    with open(file_path, encoding="UTF-8") as f:
        return f.read().strip()


def set_source_value(repo_path: pathlib.Path, value: int):
    with open(repo_path / "source.txt", "w", encoding="UTF-8") as f:
        f.write("{}\n".format(value))


def validate_copy_contents(
    enclosing_dir: pathlib.Path,
    expected_value: int,
    task1_expected_value: Optional[int] = None,
):
    for file in enclosing_dir.iterdir():
        if file.suffix != ".txt":
            continue
        contents = load_file_contents(file)
        fname = file.stem
        task_id = int(fname.split("-")[-1])
        if task1_expected_value is not None and task_id == 1:
            assert contents == "{}\n1".format(task1_expected_value)
        else:
            assert contents == "{}\n{}".format(expected_value, task_id)


def test_run_this_commit_no_git(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode != 0


def test_run_this_commit_disabled_git(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    # Disable git integration.
    with open(repo_path / CONFIG_FILE_NAME, "w", encoding="UTF-8") as file:
        file.write("disable_git = true\n")

    # This should fail because Git integration is disabled.
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode != 0


def test_run_this_commit_bare_git(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    run_git_command(repo_path, ["init"])
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode != 0


def test_again_and_this_commit_git(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    # Run once.
    initial_value = 1
    set_source_value(repo_path, initial_value)
    res = cond.run("//:copy")
    assert res.returncode == 0
    out_dir = cond.find_task_output_dir("//:copy", is_experiment=False)
    assert out_dir is not None
    validate_copy_contents(out_dir, initial_value)

    # Set both --again and --this-commit. This should fail because this flag
    # combination is contradictory.
    res = cond.run("//:copy", again=True, this_commit=True)
    assert res.returncode != 0


def test_this_commit(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    # Run once. This should succeed.
    start_value = 101
    set_source_value(repo_path, start_value)
    res = cond.run("//:copy")
    assert res.returncode == 0
    out_dir = cond.find_task_output_dir("//:copy", is_experiment=False)
    assert out_dir is not None
    validate_copy_contents(out_dir, start_value)

    # Make a new commit. Then we purposefully make one task fail.
    run_git_command(repo_path, ["commit", "--allow-empty", "-m", "Test new commit."])

    # Our fixture project will fail the `generate-1` task if this file is present.
    fail_file = repo_path / "fail"
    with open(fail_file, "w", encoding="UTF-8") as f:
        f.write("\n")

    # Run with --again. This should fail (one of the tasks will fail).
    again_value1 = 151
    set_source_value(repo_path, again_value1)
    res = cond.run("//:copy", again=True)
    assert res.returncode != 0

    # Remove the failure file marker.
    fail_file.unlink()

    # Run with --this-commit. This should succeed and should only re-run task 1.
    this_commit_value = 1337
    set_source_value(repo_path, this_commit_value)
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode == 0
    # Tasks 0 and 2 should have `again_value1`. Task 1 should have value
    # `this_commit_value`. This indicates that only task 1 was executed.
    validate_copy_contents(
        out_dir, expected_value=again_value1, task1_expected_value=this_commit_value
    )

    # Run with --again. This should succeed. All task outputs should have
    # `again_value2`.
    again_value2 = 42
    set_source_value(repo_path, again_value2)
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    validate_copy_contents(out_dir, expected_value=again_value2)


def test_this_commit_three(tmp_path: pathlib.Path):
    # This test uses the following commit history:
    #   [commit 1] --- [commit 2] --- [commit 3]
    # We run the experiments against commit 1 and 3. Then we check that
    # `--this-commit` works as expected when run against commit 2.
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    # Commit 1
    run_git_command(repo_path, ["checkout", "-b", "commit1"])
    commit1_value = 123
    set_source_value(repo_path, commit1_value)

    # Run against commit 1.
    res = cond.run("//:copy")
    assert res.returncode == 0
    out_dir = cond.find_task_output_dir("//:copy", is_experiment=False)
    assert out_dir is not None
    validate_copy_contents(out_dir, commit1_value)

    # Commit 2
    run_git_command(repo_path, ["checkout", "master"])
    run_git_command(repo_path, ["commit", "--allow-empty", "-m", "Second commit."])
    run_git_command(repo_path, ["checkout", "-b", "commit2"])
    run_git_command(repo_path, ["checkout", "master"])

    # Commit 3
    run_git_command(repo_path, ["commit", "--allow-empty", "-m", "Third commit."])
    run_git_command(repo_path, ["checkout", "-b", "commit3"])

    # Run against commit 3.
    commit3_value = 987
    set_source_value(repo_path, commit3_value)
    res = cond.run("//:copy", again=True)
    assert res.returncode == 0
    validate_copy_contents(out_dir, commit3_value)

    # Switch back to commit 2.
    commit2_value = 42
    set_source_value(repo_path, commit2_value)
    run_git_command(repo_path, ["checkout", "commit2"])

    # Running without --again should produce `commit1_value`.
    res = cond.run("//:copy")
    assert res.returncode == 0
    validate_copy_contents(out_dir, commit1_value)

    # Running with --this-commit should behave like --again.
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode == 0
    validate_copy_contents(out_dir, commit2_value)

    # Check that we select the correct relevant version for each commit.
    # Running with --this-commit should be a no-op.
    unused_value = 783
    set_source_value(repo_path, unused_value)
    run_git_command(repo_path, ["checkout", "commit1"])
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode == 0
    validate_copy_contents(out_dir, commit1_value)

    run_git_command(repo_path, ["checkout", "commit3"])
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode == 0
    validate_copy_contents(out_dir, commit3_value)

    run_git_command(repo_path, ["checkout", "commit2"])
    res = cond.run("//:copy", this_commit=True)
    assert res.returncode == 0
    validate_copy_contents(out_dir, commit2_value)


def test_invalid_commit_hash(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)
    # The commit symbol passed to `--at-least` is invalid.
    res = cond.run("//:copy", at_least="invalid")
    assert res.returncode != 0


def test_invalid_both_flags(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)
    # Cannot set both the `--at-least` and `--this-commit` flags.
    res = cond.run("//:copy", at_least="master", this_commit=True)
    assert res.returncode != 0


def test_invalid_again_at_least(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)
    # Cannot set both the `--at-least` and `--again` flags.
    res = cond.run("//:copy", at_least="master", again=True)
    assert res.returncode != 0


def test_at_least(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    # Make commit 1.
    run_git_command(repo_path, ["checkout", "-b", "commit1"])
    commit1_value = 123
    set_source_value(repo_path, commit1_value)

    # Our fixture project will fail the `generate-1` task if this file is present.
    fail_file = repo_path / "fail"
    with open(fail_file, "w", encoding="UTF-8") as f:
        f.write("\n")

    # Run against commit 1. This should fail.
    res = cond.run("//:copy")
    assert res.returncode != 0

    # Make commit 2.
    run_git_command(repo_path, ["checkout", "master"])
    run_git_command(repo_path, ["commit", "--allow-empty", "-m", "Second commit."])
    run_git_command(repo_path, ["checkout", "-b", "commit2"])

    commit2_value = 989
    set_source_value(repo_path, commit2_value)

    # Remove the failure file marker.
    fail_file.unlink()

    # Ensure we have results as new as at least `commit1`.
    res = cond.run("//:copy", at_least="commit1")
    assert res.returncode == 0

    # Task should succeed. Only `generate-1` should have ran and so it will have
    # `commit2_value`.
    out_dir = cond.find_task_output_dir("//:copy", is_experiment=False)
    assert out_dir is not None
    validate_copy_contents(
        out_dir, expected_value=commit1_value, task1_expected_value=commit2_value
    )


def test_at_least_too_new(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    # Make commit 1 and run the task.
    run_git_command(repo_path, ["checkout", "-b", "commit1"])
    commit1_value = 123
    set_source_value(repo_path, commit1_value)

    res = cond.run("//:copy")
    assert res.returncode == 0
    out_dir = cond.find_task_output_dir("//:copy", is_experiment=False)
    assert out_dir is not None
    validate_copy_contents(out_dir, commit1_value)

    # Make commit 2.
    run_git_command(repo_path, ["checkout", "master"])
    run_git_command(repo_path, ["commit", "--allow-empty", "-m", "Second commit."])
    run_git_command(repo_path, ["checkout", "-b", "commit2"])

    # Set the current commit to commit 1.
    run_git_command(repo_path, ["checkout", "commit1"])

    # This should fail because `commit2` is newer than the current commit.
    res = cond.run("//:copy", at_least="commit2")
    assert res.returncode != 0


def test_at_least_fork(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["git-commit"])
    repo_path = tmp_path / "root"
    set_up_git_repository(repo_path)

    # Make commit 1 and run the task.
    run_git_command(repo_path, ["tag", "commit1"])
    commit1_value = 123
    set_source_value(repo_path, commit1_value)

    res = cond.run("//:copy")
    assert res.returncode == 0
    out_dir = cond.find_task_output_dir("//:copy", is_experiment=False)
    assert out_dir is not None
    validate_copy_contents(out_dir, commit1_value)

    # Make commit 2.
    run_git_command(repo_path, ["checkout", "master"])
    run_git_command(repo_path, ["commit", "--allow-empty", "-m", "Second commit."])
    run_git_command(repo_path, ["tag", "commit2"])

    # Set the current commit to commit 1.
    run_git_command(repo_path, ["checkout", "commit1"])

    # Make another commit that branches from commit 1.
    run_git_command(repo_path, ["commit", "--allow-empty", "-m", "Third commit."])
    run_git_command(repo_path, ["tag", "commit3"])
    commit3_value = 567
    set_source_value(repo_path, commit3_value)

    # This should fail because `commit2` is not an ancestor of the current commit.
    res = cond.run("//:copy", at_least="commit2")
    assert res.returncode != 0

    # This should succeed and be a no-op. `commit1` is an ancestor of `commit3`.
    res = cond.run("//:copy", at_least="commit1")
    print(res.stdout)
    print(res.stderr)
    assert res.returncode == 0
    validate_copy_contents(out_dir, commit1_value)
