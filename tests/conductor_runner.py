import pathlib
import shutil
import subprocess
from typing import Optional, Iterable

from conductor.config import OUTPUT_DIR, TASK_OUTPUT_DIR_SUFFIX

# pylint: disable=subprocess-run-check


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
        self, task_identifier: str, again: bool = False
    ) -> subprocess.CompletedProcess:
        cmd = ["run", task_identifier]
        if again:
            cmd.append("--again")
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

    def restore(self, archive_path: pathlib.Path) -> subprocess.CompletedProcess:
        return self._run_command(["restore", str(archive_path)])

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
    "long-running": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "long-running"
    ).resolve(),
    "combine-test": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "combine-test"
    ).resolve(),
    "ordering-test": pathlib.Path(
        _TESTS_DIR, "fixture-projects", "ordering-test"
    ).resolve(),
}
