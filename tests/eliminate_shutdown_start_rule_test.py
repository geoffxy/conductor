import pathlib
from typing import List, Callable, Set

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES
from conductor.context import Context
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.operation import Operation
from conductor.execution.optim_rules.eliminate_shutdown_start_env import (
    EliminateShutdownStartEnv,
)
from conductor.execution.plan import ExecutionPlan
from conductor.execution.planning.planner import ExecutionPlanner
from conductor.task_types.base import TaskType
from conductor.task_types.environment import Environment
from conductor.task_types.run import RunExperiment
from conductor.task_identifier import TaskIdentifier
from .git_utils import setup_git


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


def create_git_project(project_root: pathlib.Path) -> Context:
    project_root.mkdir(exist_ok=True)
    cond_config_file = project_root / "cond_config.toml"
    cond_config_file.touch()
    setup_git(project_root, initialize=True)
    return Context(project_root)


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


def traverse_plan(plan: ExecutionPlan, visitor: Callable[[Operation], None]) -> None:
    stack = [plan.root_op]
    visited: Set[int] = set()

    while len(stack) > 0:
        op = stack.pop()
        if id(op) in visited:
            continue

        visited.add(id(op))
        visitor(op)

        stack.extend(op.exe_deps)
