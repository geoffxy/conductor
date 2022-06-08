import pathlib
import subprocess
from typing import Optional


class Git:
    """
    Provides a Python interface to `git` through the command line.
    """

    class Commit:
        def __init__(self, commit_hash: str, has_changes: bool = False):
            self._hash = commit_hash
            self._has_changes = has_changes

        @property
        def hash(self) -> str:
            return self._hash

        @property
        def has_changes(self) -> bool:
            return self._has_changes

    def __init__(self, project_root: pathlib.Path):
        self._project_root = project_root

    def is_used(self) -> bool:
        """
        Returns `True` if the project uses git.
        """
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=self._project_root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0

    def current_commit(self) -> Optional[Commit]:
        """
        Retrieves the project's current commit hash and whether or not there are
        any uncommitted changes. If the project is not using git, or if there
        are no commits (e.g., a brand new repository), then this method will
        return `None`.
        """
        curr_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if curr_commit.returncode != 0:
            # The project is not using git (or something else went wrong).
            return None

        is_clean = subprocess.run(
            ["git", "diff-index", "--quiet", "HEAD"],
            cwd=self._project_root,
            check=False,
        )
        return self.Commit(
            commit_hash=curr_commit.stdout.strip(),
            has_changes=(is_clean.returncode != 0),
        )

    def is_ancestor(self, commit_hash: str, candidate_ancestor_hash: str) -> bool:
        """
        Returns `True` if `candidate_ancestor_hash` is an ancestor of
        `commit_hash`.
        """
        result = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                candidate_ancestor_hash,
                commit_hash,
            ],
            cwd=self._project_root,
            check=False,
        )
        return result.returncode == 0

    def get_distance(self, start_hash: str, ancestor_hash: str) -> int:
        """
        Returns the number of commits away `ancestor_hash` is from `start_hash`.
        For meaningful results, `ancestor_hash` must be an ancestor of `start_hash`.
        """
        result = subprocess.run(
            ["git", "rev-list", "--count", start_hash, "^{}".format(ancestor_hash)],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to get the distance between commits.")
        return int(result.stdout.strip())

    def rev_parse(self, commit_symbol: str) -> Optional[str]:
        result = subprocess.run(
            ["git", "rev-parse", commit_symbol],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
