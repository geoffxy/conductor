import pathlib
from typing import Sequence, Optional, TYPE_CHECKING

import conductor.filename as f
from conductor.errors import InternalError
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier
from conductor.utils.run_arguments import RunArguments
from conductor.utils.run_options import RunOptions
from .base import TaskType

if TYPE_CHECKING:
    import conductor.context as c


class _RunSubprocess(TaskType):
    """
    An abstract base class representing tasks that launch a subprocess.
    """

    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
        run: str,
        args: list,
        options: dict,
        parallelizable: bool,
        env: Optional[str],
    ):
        super().__init__(
            identifier=identifier, cond_file_path=cond_file_path, deps=deps
        )
        self._args = RunArguments.from_raw(identifier, args)
        self._options = RunOptions.from_raw(identifier, options)
        self._raw_run = run
        self._run = " ".join(
            [run, self._args.serialize_cmdline(), self._options.serialize_cmdline()]
        )
        self._parallelizable = parallelizable
        self._env = self._parse_env(env)

    def __repr__(self) -> str:
        return "".join(
            [
                super().__repr__(),
                ", run=",
                self._run,
                ", parallelizable=",
                str(self._parallelizable),
                ")",
            ]
        )

    @property
    def record_output(self) -> bool:
        """
        If set to True, this task's output on stdout and stderr will be
        recorded and saved to files in the task's output directory.
        """
        raise NotImplementedError

    @property
    def parallelizable(self) -> bool:
        return self._parallelizable

    @property
    def raw_run(self) -> str:
        return self._raw_run

    @property
    def args(self) -> RunArguments:
        return self._args

    @property
    def options(self) -> RunOptions:
        return self._options

    @property
    def env(self) -> Optional[TaskIdentifier]:
        return self._env

    def _create_new_version(self, ctx: "c.Context") -> None:
        # N.B. Only `RunExperiment` is versioned.
        pass

    def _parse_env(self, candidate_env: Optional[str]) -> Optional[TaskIdentifier]:
        if candidate_env is None:
            return None
        if TaskIdentifier.is_relative_candidate(candidate_env):
            return TaskIdentifier.from_relative_str(candidate_env, self.identifier.path)
        else:
            return TaskIdentifier.from_str(candidate_env)


class RunCommand(_RunSubprocess):
    """
    Represents the `run_command()` task type.

    Runs a command using `bash`. The task's standard out and error are not
    recorded. The task's outputs are not archivable either.
    """

    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
        run: str,
        args: list,
        options: dict,
        parallelizable: bool,
        env: Optional[str],
    ):
        super().__init__(
            identifier=identifier,
            cond_file_path=cond_file_path,
            deps=deps,
            run=run,
            args=args,
            options=options,
            parallelizable=parallelizable,
            env=env,
        )

    @property
    def record_output(self) -> bool:
        return False


class RunExperiment(_RunSubprocess):
    """
    Represents the `run_experiment()` task type.

    Runs a command using `bash`. The task's standard out and error are
    recorded. The task's outputs are placed in a timestamped directory and
    are archivable.
    """

    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
        run: str,
        args: list,
        options: dict,
        parallelizable: bool,
        env: Optional[str],
    ):
        super().__init__(
            identifier=identifier,
            cond_file_path=cond_file_path,
            deps=deps,
            run=run,
            args=args,
            options=options,
            parallelizable=parallelizable,
            env=env,
        )
        self._did_retrieve_version = False
        self._most_relevant_version: Optional[Version] = None

    @property
    def archivable(self) -> bool:
        return True

    @property
    def record_output(self) -> bool:
        return True

    def get_output_path(self, ctx: "c.Context") -> Optional[pathlib.Path]:
        self._ensure_most_relevant_existing_version_computed(ctx)
        if self._most_relevant_version is None:
            return None

        unversioned_path = super().get_output_path(ctx)
        assert unversioned_path is not None
        return unversioned_path.with_name(
            f.task_output_dir(self.identifier, version=self._most_relevant_version)
        )

    def get_specific_output_path(
        self, ctx: "c.Context", version: Optional[Version]
    ) -> Optional[pathlib.Path]:
        if version is None:
            raise InternalError(
                details="Version must be specified when calling "
                "get_specific_output_path() on a RunExperiment task."
            )
        unversioned_path = super().get_output_path(ctx)
        assert unversioned_path is not None
        return unversioned_path.with_name(
            f.task_output_dir(self.identifier, version=version)
        )

    def should_run(self, ctx: "c.Context", at_least_commit: Optional[str]) -> bool:
        """
        We use the presence of a "most relevant" existing version to decide
        whether or not this task needs to execute.
        """
        self._ensure_most_relevant_existing_version_computed(ctx)
        if self._most_relevant_version is None:
            # Must run because no relevant version exists.
            return True
        if at_least_commit is None:
            # There already is a most relevant version and we are not asked to
            # run for at least some commit.
            return False
        if self._most_relevant_version.commit_hash is None:
            # Must re-run since the most relevant version does not have a commit
            # hash and `at_least_commit` is set to some commit.
            return True
        if self._most_relevant_version.commit_hash == at_least_commit:
            # No need to re-run. The most relevant version matches `at_least_commit`.
            return False

        # We are being asked to ensure there is at least a version as new as
        # `at_least_commit`. We must run if the most relevant version's commit
        # is older than the given commit. If the most relevant version's commit
        # is an ancestor of the given commit (and does not match the commit),
        # then it must be "older" (this is based on how we define the most
        # relevant version).
        most_relevant_is_older = ctx.git.is_ancestor(
            at_least_commit, self._most_relevant_version.commit_hash
        )
        if not most_relevant_is_older:
            # No need to re-run.
            return False
        else:
            # Force a re-run and ensure the most relevant version is recomputed.
            self._did_retrieve_version = False
            return True

    def create_new_version(self, ctx: "c.Context") -> Version:
        self._create_new_version(ctx)
        assert self._most_relevant_version is not None
        return self._most_relevant_version

    def _create_new_version(self, ctx: "c.Context") -> None:
        # N.B. If this task fails, the value of `most_relevant_version` will be
        # incorrect. However, any tasks that have this task as a dependency will
        # be skipped, so no incorrectness will occur. The new version will not
        # be committed into the version index.
        self._did_retrieve_version = True
        self._most_relevant_version = ctx.version_index.generate_new_output_version(
            commit=ctx.current_commit
        )

    def _ensure_most_relevant_existing_version_computed(self, ctx: "c.Context"):
        if self._did_retrieve_version:
            return
        version = self._retrieve_most_relevant_existing_version(ctx)
        self._most_relevant_version = version
        self._did_retrieve_version = True

    def _retrieve_most_relevant_existing_version(
        self, ctx: "c.Context"
    ) -> Optional[Version]:
        """
        Finds the "most relevant" existing version of this task's outputs, if
        one exists. The definition of "most relevant" depends on whether git is
        used to track the code in the project, and is governed by the logic in
        this method.

        This method is meant for internal use.
        """
        # Simple case. If the project does not use git, the most relevant
        # existing version is the latest (newest) version (if it exists).
        if not ctx.uses_git:
            res = ctx.version_index.get_latest_output_version(self._identifier)
            return res

        # Retrieve the commit hash associated with `HEAD`.
        curr_commit = ctx.current_commit

        # This case happens if the repository is bare (no commits). Then the
        # most relevant existing version is the latest version, if it exists.
        if curr_commit is None:
            return ctx.version_index.get_latest_output_version(self._identifier)

        # Retrieve all existing versions for this task. Filter them into tasks
        # with null commit hashes and ones that are ancestors.
        existing_versions = ctx.version_index.get_all_versions_for_task(
            self._identifier
        )
        ancestor_versions = []
        null_commit_versions = []
        for version in existing_versions:
            if version.commit_hash is None:
                null_commit_versions.append(version)
            elif ctx.git.is_ancestor(
                curr_commit.hash, candidate_ancestor_hash=version.commit_hash
            ):
                ancestor_versions.append(version)

        # The most relevant existing version is the one that is "closest" to the
        # current commit (measured by number of commits between them). If there
        # are multiple closest commit versions, we select the newest one.
        if len(ancestor_versions) > 0:
            selected_version = None
            closest_distance = -1
            for v in ancestor_versions:
                assert v.commit_hash is not None
                dist = ctx.git.get_distance(curr_commit.hash, v.commit_hash)
                if selected_version is None or dist < closest_distance:
                    selected_version = v
                    closest_distance = dist
                elif (
                    dist == closest_distance
                    and v.timestamp > selected_version.timestamp
                ):
                    selected_version = v
            assert selected_version is not None
            return selected_version

        # There are no ancestor commits and all existing versions do not have a
        # commit hash. We select the newest version. This maintains the same
        # behavior as Conductor v0.4.0 and older.
        if (
            len(null_commit_versions) == len(existing_versions)
            and len(null_commit_versions) > 0
        ):
            return max(null_commit_versions, key=lambda v: v.timestamp)

        # Otherwise, this means there may exist versions with commits that are
        # not ancestors of the current commit. For correctness, we should not
        # depend on the results from any previous version.
        return None
