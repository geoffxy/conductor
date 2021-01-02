import pathlib
import shutil
import subprocess

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
        return self.project_root / "cond-out"

    def run(
        self, task_identifier: str, again: bool = False
    ) -> subprocess.CompletedProcess:
        cmd = ["cond", "--debug", "run", task_identifier]
        if again:
            cmd.append("--again")
        return subprocess.run(cmd, cwd=self._project_root, capture_output=True)

    def clean(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["cond", "clean", "--force"], cwd=self._project_root, capture_output=True
        )


_TESTS_DIR = pathlib.Path(__file__).parent
EXAMPLE_TEMPLATES = {
    "hello_world": pathlib.Path(_TESTS_DIR, "..", "examples", "1-hello-world").resolve()
}
