import pathlib
import subprocess

from conductor.utils.git import Git
from conductor.config import COND_FILE_NAME
from .git_utils import setup_git, create_commit


def test_detect_no_git(tmp_path: pathlib.Path):
    g = Git(tmp_path)
    assert not g.is_used()


def test_detect_empty_repo(tmp_path: pathlib.Path):
    setup_git(tmp_path, initialize=False)
    g = Git(tmp_path)
    assert g.is_used()


def test_detect_with_commits(tmp_path: pathlib.Path):
    setup_git(tmp_path, initialize=True)
    g = Git(tmp_path)
    assert g.is_used()


def test_get_current_commit(tmp_path: pathlib.Path):
    g = Git(tmp_path)
    # No repository
    assert g.current_commit() is None

    setup_git(tmp_path, initialize=False)
    # No commits
    assert g.current_commit() is None

    # Create a commit with an empty file
    open(tmp_path / "test.txt", "w", encoding="UTF-8").close()
    results = subprocess.run(["git", "add", "test.txt"], cwd=tmp_path, check=False)
    assert results.returncode == 0
    results = subprocess.run(
        ["git", "commit", "-m", "Test commit."], cwd=tmp_path, check=False
    )
    assert results.returncode == 0

    # Fetch the commit's hash
    get_hash_results = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert get_hash_results.returncode == 0
    expected_hash = get_hash_results.stdout.strip()

    # We should retrieve the same hash
    current_commit = g.current_commit()
    assert current_commit is not None
    assert current_commit.hash == expected_hash
    assert not current_commit.has_changes

    # Making changes to the file should result in `has_changes` being set to
    # True.
    with open(tmp_path / "test.txt", "w", encoding="UTF-8") as f:
        f.write("Hello world!")
    current_commit = g.current_commit()
    assert current_commit is not None
    assert current_commit.hash == expected_hash
    assert current_commit.has_changes


def test_is_ancestor(tmp_path: pathlib.Path):
    setup_git(tmp_path, initialize=True)
    g = Git(tmp_path)

    first_commit = g.current_commit()
    assert first_commit is not None

    # A commit is an ancestor of itself.
    assert g.is_ancestor(
        commit_hash=first_commit.hash, candidate_ancestor_hash=first_commit.hash
    )

    # Create a new commit, which should be a descendant of `first_commit`.
    new_commit_hash = create_commit(tmp_path, "Branch1")
    assert g.is_ancestor(
        commit_hash=new_commit_hash, candidate_ancestor_hash=first_commit.hash
    )
    # The new commit is not an ancestor of `first_commit`
    assert not g.is_ancestor(
        commit_hash=first_commit.hash, candidate_ancestor_hash=new_commit_hash
    )

    # Create a sibling commit and check that they are not ancestors of
    # eachother.
    results = subprocess.run(
        ["git", "checkout", first_commit.hash], cwd=tmp_path, check=False
    )
    assert results.returncode == 0
    sibling_commit = create_commit(tmp_path, "Branch2")
    assert not g.is_ancestor(
        commit_hash=sibling_commit, candidate_ancestor_hash=new_commit_hash
    )
    assert not g.is_ancestor(
        commit_hash=new_commit_hash, candidate_ancestor_hash=sibling_commit
    )


def test_distance(tmp_path: pathlib.Path):
    setup_git(tmp_path, initialize=False)
    commit1 = create_commit(tmp_path, "C1")
    commit2 = create_commit(tmp_path, "C2")
    commit3 = create_commit(tmp_path, "C3")

    g = Git(tmp_path)
    assert g.get_distance(commit1, commit1) == 0
    assert g.get_distance(commit2, commit1) == 1
    assert g.get_distance(commit3, commit1) == 2
    assert g.get_distance(commit3, commit2) == 1

    assert g.is_ancestor(commit3, commit1)
    assert g.is_ancestor(commit2, commit1)
    assert g.is_ancestor(commit3, commit2)


def test_create_unpack_bundle(tmp_path: pathlib.Path):
    orig_git = tmp_path / "orig"
    orig_git.mkdir(exist_ok=True, parents=True)
    setup_git(orig_git, initialize=True)

    # Create a commit with an empty file
    open(orig_git / "test.txt", "w", encoding="UTF-8").close()
    results = subprocess.run(["git", "add", "test.txt"], cwd=orig_git, check=False)
    assert results.returncode == 0
    results = subprocess.run(
        ["git", "commit", "-m", "Test commit."], cwd=orig_git, check=False
    )
    assert results.returncode == 0

    # Create a bundle.
    g = Git(orig_git)
    g.create_bundle("HEAD", tmp_path / "test.bundle", silent=True)

    # Check that it exists
    assert (tmp_path / "test.bundle").exists()

    # Unpack the bundle
    new_git = tmp_path / "new"
    new_git.mkdir(exist_ok=True, parents=True)
    result = subprocess.run(
        ["git", "clone", str(tmp_path / "test.bundle"), str(new_git)], check=False
    )
    assert result.returncode == 0

    # Check that the file exists.
    assert (new_git / "test.txt").exists()


def test_find_cond_files(tmp_path: pathlib.Path):
    setup_git(tmp_path, initialize=True)

    # Create a few files, including nested ones.
    cond1 = tmp_path / COND_FILE_NAME
    cond1.touch()
    (tmp_path / "file.txt").touch()
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    cond2 = nested_dir / COND_FILE_NAME
    cond2.touch()
    nested_2 = nested_dir / "nested2"
    nested_2.mkdir()
    cond3 = nested_2 / COND_FILE_NAME
    cond3.touch()

    # Nothing checked in, so we should not find any files.
    g = Git(tmp_path)
    files = g.find_files([COND_FILE_NAME, f"**/{COND_FILE_NAME}"])
    assert len(files) == 0

    # Check in the files.
    result = subprocess.run(["git", "add", "."], cwd=tmp_path, check=False)
    assert result.returncode == 0
    result = subprocess.run(
        ["git", "commit", "-m", "Test commit."], cwd=tmp_path, check=False
    )
    assert result.returncode == 0

    # Now we should find the files.
    files = g.find_files([COND_FILE_NAME, f"**/{COND_FILE_NAME}"])
    assert len(files) == 3

    # Found paths will be relative to the repository root.
    expected_rel_files = [
        str(cond1.relative_to(tmp_path)),
        str(cond2.relative_to(tmp_path)),
        str(cond3.relative_to(tmp_path)),
    ]
    assert set(files) == set(expected_rel_files)
