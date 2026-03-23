import importlib.resources as pkg_resources
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from conductor.context import Context
from conductor.errors import ConductorError
from conductor.explorer.workspace import Workspace
from conductor.explorer.version_graph import compute_version_graph
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.run import RunExperiment, RunCommand
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
    ctx.use_cloned_version_index()
    ctx.task_index.load_all_known_tasks(ctx.git)
    all_results = ctx.version_index.get_all_versions()
    mapped: Dict[TaskIdentifier, List[m.ResultVersion]] = {}
    for task_id, version in all_results:
        if task_id not in mapped:
            mapped[task_id] = []
        mapped[task_id].append(m.ResultVersion.from_version(version))

    list_results = []
    for task_id, versions in mapped.items():
        # Compute the current version for this task, if relevant. The UI
        # displays this information.
        current_version = None
        task = ctx.task_index.get_task(task_id)
        if isinstance(task, RunExperiment):
            maybe_version = task.get_output_version(ctx)
            if maybe_version is not None:
                current_version = m.ResultVersion.from_version(maybe_version)
        list_results.append(
            m.TaskResults(
                identifier=m.TaskIdentifier.from_cond(task_id),
                versions=versions,
                current_version=current_version,
            )
        )

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
                runnable_details=(
                    m.TaskRunnableDetails(
                        run=task.raw_run,
                        args=task.args.serialize_str_list(),
                        options=task.options.serialize_str_dict(),
                    )
                    if isinstance(task, (RunExperiment, RunCommand))
                    else None
                ),
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


@app.get("/api/1/version_graph")
def get_version_graph(task_id: str) -> m.VersionGraph:
    """
    Retrieves a condensed commit graph for all versions of the specified task.
    """
    assert ctx is not None
    try:
        cond_task_id = TaskIdentifier.from_str(task_id)
    except ConductorError as ex:
        raise HTTPException(status_code=400, detail=ex.printable_message()) from ex

    ctx.use_cloned_version_index()
    task_versions = [
        version
        for _, version in ctx.version_index.get_versioned_tasks(
            tasks=[cond_task_id],
            latest_only=False,
        )
    ]

    graph = compute_version_graph(
        task_id=cond_task_id, versions=task_versions, git=ctx.git
    )

    # Compute the selected version for this task, if relevant. The UI
    # displays this information.
    task_identifier = TaskIdentifier.from_str(task_id)
    task = ctx.task_index.get_task(task_identifier)
    if isinstance(task, RunExperiment):
        maybe_version = task.get_output_version(ctx)
        if maybe_version is not None:
            selected_version = m.ResultVersion.from_version(maybe_version)
            graph.selected_version = selected_version

    return graph


@app.get("/api/1/commit_info")
def get_commit_info(commit_hash: str) -> m.CommitInfo:
    """
    Retrieves detailed information for a specific git commit.
    """
    assert ctx is not None
    try:
        commit = ctx.git.get_commit_info(commit_hash)
    except RuntimeError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex

    return m.CommitInfo.from_cond(commit)


# Serve the static pages.
# Note that this should go last as a "catch all" route.
explorer_module_pkg = pkg_resources.files(explorer_module)
with pkg_resources.as_file(explorer_module_pkg) as explorer_module_path:
    # Make sure the directory exists. This is needed for our test environments
    # where we do not build the explorer UI. The file is supposed to exist as a
    # symlink.
    static_dir = explorer_module_path / "static"
    if not static_dir.exists():
        static_dir.mkdir(exist_ok=True)
    app.mount(
        "/",
        StaticFiles(directory=static_dir, html=True),
        name="static",
    )
