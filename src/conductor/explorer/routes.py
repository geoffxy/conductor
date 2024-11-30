import importlib.resources as pkg_resources
from typing import Optional, List, Dict

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from conductor.context import Context
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier
import conductor.explorer as explorer_module

# Conductor's explorer API requires access to a `Context` instance. This must be
# set globally before the API is used. Note that this means only one API
# instance can run at a time, but that is acceptable for our use case.
ctx: Optional[Context] = None
app = FastAPI()


def set_context(context: Context) -> None:
    """
    Sets the global context for the explorer API.
    """
    global ctx  # pylint: disable=global-statement
    ctx = context


class ResultVersion(BaseModel):
    timestamp: int
    commit_hash: Optional[str]
    has_uncommitted_changes: bool

    @classmethod
    def from_version(cls, version: Version) -> "ResultVersion":
        return cls(
            timestamp=version.timestamp,
            commit_hash=version.commit_hash,
            has_uncommitted_changes=version.has_uncommitted_changes,
        )


class TaskResults(BaseModel):
    identifier: str
    versions: List[ResultVersion]


@app.get("/api/1/results/all_versions")
def get_all_versions() -> List[TaskResults]:
    """
    Retrieve all versioned results that Conductor manages.
    """
    assert ctx is not None
    version_index = ctx.version_index.clone()
    all_results = version_index.get_all_versions()
    mapped: Dict[TaskIdentifier, List[ResultVersion]] = {}
    for task_id, version in all_results:
        if task_id not in mapped:
            mapped[task_id] = []
        mapped[task_id].append(ResultVersion.from_version(version))
    list_results = [
        TaskResults(identifier=str(task_id), versions=versions)
        for task_id, versions in mapped.items()
    ]
    list_results.sort(key=lambda r: r.identifier)
    return list_results



# Serve the static pages.
# Note that this should go last as a "catch all" route.
explorer_module_pkg = pkg_resources.files(explorer_module)
with pkg_resources.as_file(explorer_module_pkg) as explorer_module_path:
    app.mount(
        "/",
        StaticFiles(directory=explorer_module_path / "static", html=True),
        name="static",
    )
