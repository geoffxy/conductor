import pathlib

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.operation import Operation
from conductor.execution.ops.transfer_repo import TransferRepo
from conductor.execution.optim_rules.join_sibling_envs import JoinSiblingEnvs
from conductor.execution.optim_rules.eliminate_transfer_repos import (
    EliminateTransferRepos,
)
from conductor.execution.optim_rules.eliminate_shutdown_start_env import (
    EliminateShutdownStartEnv,
)
from conductor.execution.optim_rules.utils import traverse_plan
from conductor.execution.planning.planner import ExecutionPlanner
from conductor.task_identifier import TaskIdentifier
from .git_utils import create_git_project


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
    num_xfer = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown, num_xfer
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1
        elif isinstance(op, TransferRepo):
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer == 1

    rule = EliminateTransferRepos()
    changed, new_plan = rule.apply(raw_plan)
    assert not changed

    num_start = 0
    num_shutdown = 0
    num_xfer = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer == 1


def test_simple_group(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//groups:test_group")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    # group() plus the 3 run_experiment() tasks
    assert raw_plan.num_tasks_to_run == 4
    num_start = 0
    num_shutdown = 0
    num_xfer = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown, num_xfer
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1
        elif isinstance(op, TransferRepo):
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 3
    assert num_shutdown == 3
    assert num_xfer == 3

    rule1 = JoinSiblingEnvs()
    rule2 = EliminateTransferRepos()
    changed, new_plan = rule1.apply(raw_plan)
    assert changed
    changed, new_plan = rule2.apply(new_plan)
    assert changed

    num_start = 0
    num_shutdown = 0
    num_xfer = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer == 1


def test_run_expt_group(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//groups:complex1")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    # Experiments plus combine
    assert raw_plan.num_tasks_to_run == 4
    num_start = 0
    num_shutdown = 0
    num_xfer = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown, num_xfer
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1
        elif isinstance(op, TransferRepo):
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 3
    assert num_shutdown == 3
    assert num_xfer == 3

    rule1 = JoinSiblingEnvs()
    rule2 = EliminateTransferRepos()
    changed, new_plan = rule1.apply(raw_plan)
    assert changed
    changed, new_plan = rule2.apply(new_plan)
    assert changed

    num_start = 0
    num_shutdown = 0
    num_xfer = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer == 1


def test_complex_group(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//groups:complex")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    # 3 experiments per group (2 groups), 2 combines, 1 group
    assert raw_plan.num_tasks_to_run == 9
    num_start = 0
    num_shutdown = 0
    num_xfer = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown, num_xfer
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1
        elif isinstance(op, TransferRepo):
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 6
    assert num_shutdown == 6
    assert num_xfer == 6

    rule1 = JoinSiblingEnvs()
    rule2 = EliminateTransferRepos()
    changed, new_plan = rule1.apply(raw_plan)
    assert changed
    changed, new_plan = rule2.apply(raw_plan)

    num_start = 0
    num_shutdown = 0
    num_xfer = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 2
    assert num_shutdown == 2
    assert num_xfer == 2

    # Apply the rule again. We should be able to unify the two experiment groups.
    changed, new_plan = rule1.apply(new_plan)
    assert changed
    changed, new_plan = rule2.apply(new_plan)
    assert changed

    num_start = 0
    num_shutdown = 0
    num_xfer = 0
    traverse_plan(new_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer == 1

    # No more changes if applied a third time.
    changed, _ = rule1.apply(new_plan)
    assert not changed
    changed, _ = rule2.apply(new_plan)
    assert not changed


def test_with_no_env(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//xfer_results:partial")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    # The task graph looks like this:
    #
    # partial (env) <-- simple2 (env) <-- base_simple2 (env)
    #    ^------------- non_env
    #
    # After creating the initial plan, we will transfer results for `simple2`
    # and `non_env`. After applying the optimization rules, we should remove the
    # transfer for `simple2`.

    assert raw_plan.num_tasks_to_run == 4
    num_xfer = 0

    def visitor(op: Operation) -> None:
        nonlocal num_xfer
        if isinstance(op, TransferRepo):
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_xfer == 3

    # We need to apply `EliminateShutdownStartEnv` first to eliminate the extra
    # start/shutdown env ops before `EliminateTransferRepos` can take effect.
    rule1 = EliminateShutdownStartEnv()
    rule2 = EliminateTransferRepos()
    changed, new_plan = rule1.apply(raw_plan)
    assert changed
    changed, new_plan = rule2.apply(new_plan)
    assert changed

    # There should only be one transfer repo op.
    num_xfer = 0
    traverse_plan(raw_plan, visitor)
    assert num_xfer == 1

    # No further changes.
    changed, _ = rule1.apply(new_plan)
    assert not changed
    changed, _ = rule2.apply(new_plan)
    assert not changed
