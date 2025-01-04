import pathlib

from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES
from conductor.execution.ops.operation import Operation
from conductor.execution.ops.transfer_results import TransferResults, TransferDirection
from conductor.execution.optim_rules.eliminate_dep_transfers import (
    EliminateDepTransfers,
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
    task_id = TaskIdentifier.from_str("//xfer_results:simple")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    assert raw_plan.num_tasks_to_run == 2
    num_xfer = 0

    def visitor(op: Operation) -> None:
        nonlocal num_xfer
        if isinstance(op, TransferResults) and op.direction == TransferDirection.ToEnv:
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_xfer == 1

    rule = EliminateDepTransfers()
    changed, new_plan = rule.apply(raw_plan)
    assert not changed

    num_xfer = 0
    traverse_plan(new_plan, visitor)
    assert num_xfer == 1


def test_simple_removal(tmp_path: pathlib.Path) -> None:
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["remote-envs"])
    ctx = create_git_project(cond.project_root)
    task_id = TaskIdentifier.from_str("//xfer_results:simple2")
    ctx.task_index.load_transitive_closure(task_id)
    planner = ExecutionPlanner(ctx)
    raw_plan = planner.create_plan_for(task_id)

    assert raw_plan.num_tasks_to_run == 2
    num_xfer = 0

    def visitor(op: Operation) -> None:
        nonlocal num_xfer
        if isinstance(op, TransferResults) and op.direction == TransferDirection.ToEnv:
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_xfer == 1

    # We need to apply `EliminateShutdownStartEnv` first to eliminate the extra
    # start/shutdown env ops before `EliminateDepTransfers` can take effect.
    rule1 = EliminateShutdownStartEnv()
    rule2 = EliminateDepTransfers()
    changed, new_plan = rule1.apply(raw_plan)
    assert changed
    changed, new_plan = rule2.apply(new_plan)
    assert changed

    num_xfer = 0
    traverse_plan(new_plan, visitor)
    assert num_xfer == 0


def test_partial_removal(tmp_path: pathlib.Path) -> None:
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
        if isinstance(op, TransferResults) and op.direction == TransferDirection.ToEnv:
            num_xfer += 1

    traverse_plan(raw_plan, visitor)
    assert num_xfer == 2

    # We need to apply `EliminateShutdownStartEnv` first to eliminate the extra
    # start/shutdown env ops before `EliminateDepTransfers` can take effect.
    rule1 = EliminateShutdownStartEnv()
    rule2 = EliminateDepTransfers()
    changed, new_plan = rule1.apply(raw_plan)
    assert changed

    changed, new_plan = rule2.apply(new_plan)
    assert changed

    rel_xfers = []

    def find_xfer_visitor(op: Operation) -> None:
        nonlocal rel_xfers
        if isinstance(op, TransferResults) and op.direction == TransferDirection.ToEnv:
            rel_xfers.append(op)

    traverse_plan(new_plan, find_xfer_visitor)
    assert len(rel_xfers) == 1

    rel_op = rel_xfers[0]
    assert isinstance(rel_op, TransferResults)
    assert len(rel_op.unversioned_tasks) == 0
    assert len(rel_op.versioned_tasks) == 1
    expected_task_id = TaskIdentifier.from_str("//xfer_results:non_env")
    assert rel_op.versioned_tasks[0][0] == expected_task_id

    # No further changes
    changed, _ = rule1.apply(new_plan)
    assert not changed
    changed, _ = rule2.apply(new_plan)
    assert not changed
