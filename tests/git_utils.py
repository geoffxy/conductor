import pathlib
import subprocess


def setup_git(repository_root: pathlib.Path, initialize: bool):
    results = subprocess.run(["git", "init"], cwd=repository_root, check=False)
    assert results.returncode == 0
    if initialize:
        results = subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial commit"],
            cwd=repository_root,
            check=False,
        )
        assert results.returncode == 0


def create_commit(repository_root: pathlib.Path, message: str) -> str:
    commit_results = subprocess.run(
        ["git", "commit", "--allow-empty", "-m", message],
        cwd=repository_root,
        check=False,
    )
    assert commit_results.returncode == 0
    # Fetch the commit's hash
    get_hash_results = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert get_hash_results.returncode == 0
    return get_hash_results.stdout.strip()
