import pathlib
from typing import List

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES
from conductor.context import Context
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.operation import Operation
from conductor.execution.optim_rules.eliminate_shutdown_start_env import (
    EliminateShutdownStartEnv,
)
from conductor.execution.optim_rules.utils import traverse_plan
from conductor.execution.planning.planner import ExecutionPlanner
from conductor.task_types.base import TaskType
from conductor.task_types.environment import Environment
from conductor.task_types.run import RunExperiment
from conductor.task_identifier import TaskIdentifier
from .git_utils import create_git_project


def test_simple_no_change_manual(tmp_path: pathlib.Path) -> None:
    project_root = tmp_path / "root"
    ctx = create_git_project(project_root)
    env_id = TaskIdentifier.from_str("//:test_env")
    run_id = TaskIdentifier.from_str("//:run")
    env = Environment(
        identifier=env_id,
        cond_file_path=project_root,
        start=None,
        stop=None,
        connect_config="",
        deps=[],
    )
    run = RunExperiment(
        identifier=run_id,
        cond_file_path=project_root,
        deps=[],
        run="",
        args=[],
        options={},
        parallelizable=False,
        env=str(env_id),
    )
    add_to_task_index(ctx, [run], [env])

    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(run_id)
    assert raw_plan.num_tasks_to_run == 1

    num_start = 0
    num_shutdown = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1

    rule = EliminateShutdownStartEnv()
    changed, new_plan = rule.apply(raw_plan)

    assert not changed
    num_start = 0
    num_shutdown = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1


def test_simple_no_change(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//single:test")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    assert raw_plan.num_tasks_to_run == 1
    num_start = 0
    num_shutdown = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1

    rule = EliminateShutdownStartEnv()
    changed, new_plan = rule.apply(raw_plan)
    assert not changed

    num_start = 0
    num_shutdown = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1


def test_simple_double(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//double:test_second")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    assert raw_plan.num_tasks_to_run == 2
    num_start = 0
    num_shutdown = 0

    def visitor(op: Operation) -> None:
        print("visiting", str(op))
        nonlocal num_start, num_shutdown
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 2
    assert num_shutdown == 2

    rule = EliminateShutdownStartEnv()
    changed, new_plan = rule.apply(raw_plan)
    assert changed

    num_start = 0
    num_shutdown = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1


def test_simple_multi(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//double:test_third")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    assert raw_plan.num_tasks_to_run == 4
    num_start = 0
    num_shutdown = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 3
    assert num_shutdown == 3

    rule = EliminateShutdownStartEnv()
    changed, new_plan = rule.apply(raw_plan)
    assert changed

    num_start = 0
    num_shutdown = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1


def add_to_task_index(
    ctx: Context, tasks: List[TaskType], envs: List[Environment]
) -> None:
    for task in tasks:
        # pylint: disable-next=protected-access
        ctx.task_index._loaded_tasks[task.identifier] = task
    for env in envs:
        # pylint: disable-next=protected-access
        ctx.task_index._loaded_tasks[env.identifier] = env
        # pylint: disable-next=protected-access
        ctx.task_index._loaded_envs[env.identifier.name] = env
