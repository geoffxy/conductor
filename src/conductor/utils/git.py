import pathlib
import subprocess
import datetime
from typing import Optional, List


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

    class DetailedCommit:
        def __init__(
            self,
            commit_hash: str,
            date: datetime.datetime,
            message: str,
            lines_added: int,
            lines_removed: int,
        ):
            self._hash = commit_hash
            self._date = date
            self._message = message
            self._lines_added = lines_added
            self._lines_removed = lines_removed

        @property
        def hash(self) -> str:
            return self._hash

        @property
        def date(self) -> datetime.datetime:
            return self._date

        @property
        def message(self) -> str:
            return self._message

        @property
        def lines_added(self) -> int:
            return self._lines_added

        @property
        def lines_removed(self) -> int:
            return self._lines_removed

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

    def git_root(self) -> Optional[pathlib.Path]:
        """
        Returns an absolute path to the root directory of the git repository, if
        the project is using Git. Otherwise, returns `None`.

        The root directory of the repository is not necessarily the same as the
        project root (e.g., if the Conductor project is defined in a
        subdirectory of the current repository).
        """
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-dir"],
            cwd=self._project_root,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            return None
        return pathlib.Path(result.stdout.decode("utf-8")).parent

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

    def create_bundle(
        self, symbol: str, bundle_path: pathlib.Path, silent: bool = True
    ) -> bool:
        """
        Creates a bundle file containing the specified commit symbol (e.g.,
        hash, tag, branch) and saves it to `bundle_path`. Returns `True` if the
        operation was successful.
        """
        if silent:
            kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        else:
            kwargs = {}
        result = subprocess.run(
            ["git", "bundle", "create", str(bundle_path), symbol],
            cwd=self._project_root,
            check=False,
            **kwargs,  # type: ignore
        )
        return result.returncode == 0

    def find_files(self, file_patterns: List[str]) -> List[str]:
        """
        Returns a list of files in the project that match the specified pattern.
        The file paths will be relative to the repository root.
        """
        result = subprocess.run(
            ["git", "ls-files", *file_patterns],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().splitlines()

    def get_common_ancestor(self, commit_hashes: List[str]) -> Optional[str]:
        """
        Returns the hash of the most recent common ancestor of the specified
        commits. If there is no common ancestor, or if any of the specified
        commits do not exist, then this method returns `None`.
        """
        result = subprocess.run(
            ["git", "merge-base", "--octopus", *commit_hashes],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def get_raw_version_graph(
        self, commit_hashes: List[str], terminate_hash: str
    ) -> List[str]:
        """
        Returns a list of lines representing the raw version graph of the
        specified commits, starting from the commits in `commit_hashes` and
        going back in history until reaching `terminate_hash`.

        The output will need to be parsed.
        """
        result = subprocess.run(
            [
                "git",
                "rev-list",
                "--parents",
                "--boundary",
                "--format=%m%H %P | %s",
                *commit_hashes,
                f"^{terminate_hash}",
            ],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().splitlines()

    def get_commit_info(self, commit_hash: str) -> DetailedCommit:
        result = subprocess.run(
            [
                "git",
                "show",
                commit_hash,
                "--quiet",
                "--date=iso-strict",
                "--format=%aI%n%B",
                "--numstat",
            ],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stdout}")

        # Parse output (lines, commit message, changes).
        lines = result.stdout.strip().splitlines()
        commit_date = datetime.datetime.fromisoformat(lines[0])

        message_parts = []
        added = 0
        removed = 0
        for line in lines[1:]:
            parts = line.split("\t")
            # numstat format is: added \t removed \t filename
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                added += int(parts[0])
                removed += int(parts[1])
            elif line.strip():
                message_parts.append(line)

        return self.DetailedCommit(
            commit_hash=commit_hash,
            date=commit_date,
            message="\n".join(message_parts).strip(),
            lines_added=added,
            lines_removed=removed,
        )
