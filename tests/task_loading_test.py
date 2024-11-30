import pathlib
import pytest
import subprocess
from conductor.parsing.task_index import TaskIndex
from conductor.utils.git import Git
from conductor.errors import CyclicDependency, TaskNotFound

from .git_utils import setup_git, create_commit
from .conductor_runner import ConductorRunner, EXAMPLE_TEMPLATES, FIXTURE_TEMPLATES


def test_overall_loading(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["dependencies"])
    setup_git(cond.project_root, initialize=True)
    result = subprocess.run(["git", "add", "."], cwd=cond.project_root, check=False)
    assert result.returncode == 0
    create_commit(cond.project_root, "Add project files")

    git = Git(cond.project_root)
    task_index = TaskIndex(cond.project_root)
    load_results = task_index.load_all_known_tasks(git)
    assert len(load_results) == 2  # 2 COND files
    num_loaded_tasks = sum([num_loaded for _, num_loaded, _ in load_results])
    assert num_loaded_tasks == 3  # 3 tasks in total

    root_tasks = task_index.validate_all_loaded_tasks()
    assert len(root_tasks) == 1
    assert str(root_tasks[0]) == "//figures:graph"

    # Running the load a second time should be a no-op.
    load_results = task_index.load_all_known_tasks(git)
    assert len(load_results) == 0


def test_cyclic_deps_loading(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["cyclic-deps"])
    setup_git(cond.project_root, initialize=True)
    result = subprocess.run(["git", "add", "."], cwd=cond.project_root, check=False)
    assert result.returncode == 0
    create_commit(cond.project_root, "Add project files")

    git = Git(cond.project_root)
    task_index = TaskIndex(cond.project_root)
    load_results = task_index.load_all_known_tasks(git)
    assert len(load_results) == 3  # 3 COND files
    num_loaded_tasks = sum([num_loaded for _, num_loaded, _ in load_results])
    assert num_loaded_tasks == 3  # 3 tasks in total

    with pytest.raises(CyclicDependency):
        task_index.validate_all_loaded_tasks()


def test_missing_deps_loading(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["missing-deps"])
    setup_git(cond.project_root, initialize=True)
    result = subprocess.run(["git", "add", "."], cwd=cond.project_root, check=False)
    assert result.returncode == 0
    create_commit(cond.project_root, "Add project files")

    git = Git(cond.project_root)
    task_index = TaskIndex(cond.project_root)
    load_results = task_index.load_all_known_tasks(git)
    assert len(load_results) == 2  # 2 COND files
    num_loaded_tasks = sum([num_loaded for _, num_loaded, _ in load_results])
    assert num_loaded_tasks == 2  # 2 tasks in total

    with pytest.raises(TaskNotFound) as ex:
        task_index.validate_all_loaded_tasks()
        assert ex.value.task_identifier == "//mod2:test2"
