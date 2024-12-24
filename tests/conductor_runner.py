import pathlib
import re
import shutil
import subprocess
from typing import Optional, Iterable

from conductor.config import OUTPUT_DIR, TASK_OUTPUT_DIR_SUFFIX
from conductor.task_identifier import IDENTIFIER_GROUP, TaskIdentifier

# pylint: disable=subprocess-run-check

TASK_SUFFIX_REGEX = TASK_OUTPUT_DIR_SUFFIX.replace(".", "\\.")
RUN_COMMAND_DIR_REGEX = re.compile(
    "(?P<name>{ident}){task_suffix}".format(
        ident=IDENTIFIER_GROUP, task_suffix=TASK_SUFFIX_REGEX
    )
)
RUN_EXPERIMENT_DIR_REGEX = re.compile(
    "(?P<name>{ident}){task_suffix}\\.(?P<timestamp>[1-9][0-9]*)".format(
        ident=IDENTIFIER_GROUP, task_suffix=TASK_SUFFIX_REGEX
    )
)


class ConductorRunner:
    def __init__(self, project_root: pathlib.Path):
        self._project_root = project_root
        shutil.rmtree(self.output_path, ignore_errors=True)

    @classmethod
    def from_template(
        cls, dest_path: pathlib.Path, template_path: pathlib.Path
    ) -> "ConductorRunner":
        project_root = dest_path / "root"
        shutil.copytree(template_path, project_root)
        return cls(project_root)

    @property
    def project_root(self) -> pathlib.Path:
        return self._project_root

    @property
    def output_path(self) -> pathlib.Path:
        return self.project_root / OUTPUT_DIR

    def run(
        self,
        task_identifier: str,
        again: bool = False,
        stop_early: bool = False,
        jobs: Optional[int] = None,
        this_commit: bool = False,
        at_least: Optional[str] = None,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        cmd = ["run", task_identifier]
        if again:
            cmd.append("--again")
        if stop_early:
            cmd.append("--stop-early")
        if jobs is not None:
            cmd.append("--jobs")
            cmd.append(str(jobs))
        if this_commit:
            cmd.append("--this-commit")
        if at_least is not None:
            cmd.append("--at-least")
            cmd.append(at_least)
        if check:
            cmd.append("--check")
        return self._run_command(cmd)

    def clean(self) -> subprocess.CompletedProcess:
        return self._run_command(["clean", "--force"])

    def archive(
        self,
        task_identifier: Optional[str],
        output_path: Optional[pathlib.Path],
        latest: bool,
    ) -> subprocess.CompletedProcess:
        cmd = ["archive"]
        if task_identifier is not None:
            cmd.append(str(task_identifier))
        if output_path is not None:
            cmd.extend(["--output", str(output_path)])
        if latest:
            cmd.append("--latest")
        return self._run_command(cmd)

    def restore(
        self, archive_path: pathlib.Path, strict: bool
    ) -> subprocess.CompletedProcess:
        cmd = ["restore", str(archive_path)]
        if strict:
            cmd.append("--strict")
        return self._run_command(cmd)

    def gc(
        self, dry_run: bool = False, verbose: bool = False
    ) -> subprocess.CompletedProcess:
        cmd = ["gc"]
        if dry_run:
            cmd.append("--dry-run")
        if verbose:
            cmd.append("--verbose")
        return self._run_command(cmd)

    def where(
        self, task_identifier: str, project: bool = False, non_existent_ok: bool = False
    ):
        cmd = ["where", task_identifier]
        if project:
            cmd.append("--project")
        if non_existent_ok:
            cmd.append("--non-existent-ok")
        return self._run_command(cmd)

    def find_task_output_dir(
        self, task_identifier: str, is_experiment: bool = True
    ) -> Optional[pathlib.Path]:
        """Returns a path to the task's output directory, if it is found."""

        identifier = TaskIdentifier.from_str(task_identifier)
        containing_dir = self.output_path / identifier.path

        for inner_dir in containing_dir.iterdir():
            if not inner_dir.is_dir():
                continue
            match = (
                RUN_EXPERIMENT_DIR_REGEX.match(inner_dir.name)
                if is_experiment
                else RUN_COMMAND_DIR_REGEX.match(inner_dir.name)
            )
            if match is None:
                continue
            if match.group("name") == identifier.name:
                return inner_dir

        return None

    def _run_command(self, args: Iterable[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["cond", "--debug", *args], cwd=self._project_root, capture_output=True
        )


def count_task_outputs(in_dir: pathlib.Path):
    num_outputs = 0
    for file in in_dir.iterdir():
        if file.is_dir() and TASK_OUTPUT_DIR_SUFFIX in file.name:
            num_outputs += 1
    return num_outputs


_TESTS_DIR = pathlib.Path(__file__).parent

EXAMPLE_TEMPLATES = {
    "hello_world": pathlib.Path(
        _TESTS_DIR, "..", "examples", "1-hello-world"
    ).resolve(),
    "dependencies": pathlib.Path(
        _TESTS_DIR, "..", "examples", "2-dependencies"
    ).resolve(),
}

FIXTURE_TEMPLATES = {
    "combine-test": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "combine-test"
    ).resolve(),
    "experiments": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "experiments"
    ).resolve(),
    "long-running": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "long-running"
    ).resolve(),
    "ordering-test": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "ordering-test"
    ).resolve(),
    "output-recording": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "output-recording"
    ).resolve(),
    "partial-success": pathlib.Path(_TESTS_DIR, "fixture-projects", "partial-success"),
    "lib-test": pathlib.Path(_TESTS_DIR, "fixture-projects", "lib-test"),
    "git-context": pathlib.Path(_TESTS_DIR, "fixture-projects", "git-context"),
    "git-commit": pathlib.Path(_TESTS_DIR, "fixture-projects", "git-commit"),
    "include": pathlib.Path(_TESTS_DIR, "fixture-projects", "include"),
    "cyclic-deps": pathlib.Path(_TESTS_DIR, "fixture-projects", "cyclic-deps"),
    "missing-deps": pathlib.Path(_TESTS_DIR, "fixture-projects", "missing-deps"),
}
