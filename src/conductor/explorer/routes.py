import importlib.resources as pkg_resources
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from conductor.context import Context
from conductor.errors import ConductorError
from conductor.explorer.workspace import Workspace
from conductor.task_identifier import TaskIdentifier
import conductor.explorer as explorer_module
import conductor.explorer.models as m

# Conductor's explorer API requires access to a `Context` instance. This must be
# set globally before the API is used. Note that this means only one API
# instance can run at a time, but that is acceptable for our use case.
ctx: Optional[Context] = None
workspace = Workspace()
app = FastAPI()


def set_context(context: Context) -> None:
    """
    Sets the global context for the explorer API.
    """
    global ctx  # pylint: disable=global-statement
    ctx = context


@app.get("/api/1/results/all_versions")
def get_all_versions() -> List[m.TaskResults]:
    """
    Retrieve all versioned results that Conductor manages.
    """
    assert ctx is not None
    version_index = ctx.version_index.clone()
    all_results = version_index.get_all_versions()
    mapped: Dict[TaskIdentifier, List[m.ResultVersion]] = {}
    for task_id, version in all_results:
        if task_id not in mapped:
            mapped[task_id] = []
        mapped[task_id].append(m.ResultVersion.from_version(version))
    list_results = [
        m.TaskResults(identifier=m.TaskIdentifier.from_cond(task_id), versions=versions)
        for task_id, versions in mapped.items()
    ]
    list_results.sort(key=lambda r: r.identifier.display)
    return list_results


@app.get("/api/1/task_graph")
def get_task_graph() -> m.TaskGraph:
    """
    Retrieves the entire known task graph.
    """
    assert ctx is not None
    index = ctx.task_index
    index.load_all_known_tasks(ctx.git)
    try:
        if workspace.root_task_ids is None:
            root_task_ids = index.validate_all_loaded_tasks()
            workspace.set_root_task_ids(root_task_ids)
        else:
            root_task_ids = workspace.root_task_ids
        tasks = [
            m.Task(
                task_type=m.TaskType.from_cond(task),
                identifier=m.TaskIdentifier.from_cond(task.identifier),
                deps=[m.TaskIdentifier.from_cond(dep) for dep in task.deps],
            )
            for _, task in index.get_all_loaded_tasks().items()
        ]
        return m.TaskGraph(
            tasks=tasks,
            root_tasks=[
                m.TaskIdentifier.from_cond(task_id) for task_id in root_task_ids
            ],
        )
    except ConductorError as ex:
        raise HTTPException(status_code=400, detail=ex.printable_message()) from ex


# Serve the static pages.
# Note that this should go last as a "catch all" route.
explorer_module_pkg = pkg_resources.files(explorer_module)
with pkg_resources.as_file(explorer_module_pkg) as explorer_module_path:
    app.mount(
        "/",
        StaticFiles(directory=explorer_module_path / "static", html=True),
        name="static",
    )
