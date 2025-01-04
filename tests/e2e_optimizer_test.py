import pathlib

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.operation import Operation
from conductor.execution.ops.transfer_repo import TransferRepo
from conductor.execution.ops.transfer_results import TransferResults, TransferDirection
from conductor.execution.optim_rules.join_sibling_envs import JoinSiblingEnvs
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
    raw_plan = planner.create_plan_for(task_id, run_again=True)

    assert raw_plan.num_tasks_to_run == 1
    num_start = 0
    num_shutdown = 0
    num_xfer_repo = 0
    num_xfer_to_env = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown, num_xfer_repo, num_xfer_to_env
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1
        elif isinstance(op, TransferRepo):
            num_xfer_repo += 1
        elif (
            isinstance(op, TransferResults) and op.direction == TransferDirection.ToEnv
        ):
            num_xfer_to_env += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer_repo == 1
    assert num_xfer_to_env == 0

    optim_plan = planner.create_optimized_plan_for(task_id, run_again=True)

    num_start = 0
    num_shutdown = 0
    num_xfer_repo = 0
    num_xfer_to_env = 0
    traverse_plan(optim_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer_repo == 1
    assert num_xfer_to_env == 0


def test_complex_all_env(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//groups:complex")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id, run_again=True)

    # 3 experiments per group (2 groups), 2 combines, 1 group
    assert raw_plan.num_tasks_to_run == 9

    num_start = 0
    num_shutdown = 0
    num_xfer_repo = 0
    num_xfer_to_env = 0
    num_xfer_from_env = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown, num_xfer_repo, num_xfer_to_env, num_xfer_from_env
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1
        elif isinstance(op, TransferRepo):
            num_xfer_repo += 1
        elif (
            isinstance(op, TransferResults) and op.direction == TransferDirection.ToEnv
        ):
            num_xfer_to_env += 1
        elif (
            isinstance(op, TransferResults)
            and op.direction == TransferDirection.FromEnv
        ):
            num_xfer_from_env += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 6
    assert num_shutdown == 6
    assert num_xfer_repo == 6
    assert num_xfer_to_env == 0
    assert num_xfer_from_env == 6

    optim_plan = planner.create_optimized_plan_for(task_id, run_again=True)

    num_start = 0
    num_shutdown = 0
    num_xfer_repo = 0
    num_xfer_to_env = 0
    num_xfer_from_env = 0
    traverse_plan(optim_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer_repo == 1
    assert num_xfer_to_env == 0
    assert num_xfer_from_env == 6


def test_partial_env_deps(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//xfer_results:partial")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id, run_again=True)

    # The task graph looks like this:
    #
    # partial (env) <-- simple2 (env) <-- base_simple2 (env)
    #    ^------------- non_env
    #
    # After creating the initial plan, we will transfer results for `simple2`
    # and `non_env`. After applying the optimization rules, we should remove the
    # transfer for `simple2`.

    assert raw_plan.num_tasks_to_run == 4

    num_start = 0
    num_shutdown = 0
    num_xfer_repo = 0
    num_xfer_to_env = 0
    num_xfer_from_env = 0

    def visitor(op: Operation) -> None:
        nonlocal num_start, num_shutdown, num_xfer_repo, num_xfer_to_env, num_xfer_from_env
        if isinstance(op, StartRemoteEnv):
            num_start += 1
        elif isinstance(op, ShutdownRemoteEnv):
            num_shutdown += 1
        elif isinstance(op, TransferRepo):
            num_xfer_repo += 1
        elif (
            isinstance(op, TransferResults) and op.direction == TransferDirection.ToEnv
        ):
            num_xfer_to_env += 1
        elif (
            isinstance(op, TransferResults)
            and op.direction == TransferDirection.FromEnv
        ):
            num_xfer_from_env += 1

    traverse_plan(raw_plan, visitor)
    assert num_start == 3
    assert num_shutdown == 3
    assert num_xfer_repo == 3
    assert num_xfer_to_env == 2
    assert num_xfer_from_env == 3

    optim_plan = planner.create_optimized_plan_for(task_id, run_again=True)

    num_start = 0
    num_shutdown = 0
    num_xfer_repo = 0
    num_xfer_to_env = 0
    num_xfer_from_env = 0
    traverse_plan(optim_plan, visitor)
    assert num_start == 1
    assert num_shutdown == 1
    assert num_xfer_repo == 1
    assert num_xfer_to_env == 1
    assert num_xfer_from_env == 3
