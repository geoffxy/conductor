import pathlib
from typing import Tuple, List

from conductor.execution.ops.noop import NoOp
from conductor.execution.ops.operation import Operation
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.optim_rules.utils import unlink_op
from conductor.execution.operation_state import OperationState
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType
from conductor.task_types.group import Group


def test_unlink_op_single():
    _, _, op = get_noop_fixture("//:task1")
    assert len(op.deps_of) == 0
    assert len(op.exe_deps) == 0
    unlink_op(op)
    assert len(op.deps_of) == 0
    assert len(op.exe_deps) == 0


def test_unlink_op_start():
    op_list = get_three_ops_fixture()
    start_op, noop, shutdown_op = op_list
    unlink_op(start_op)
    assert len(noop.exe_deps) == 0
    assert len(noop.deps_of) == 1
    assert noop.deps_of[0] == shutdown_op
    assert len(shutdown_op.exe_deps) == 1
    assert shutdown_op.exe_deps[0] == noop
    assert len(shutdown_op.deps_of) == 0


def test_unlink_op_middle():
    op_list = get_three_ops_fixture()
    start_op, noop, shutdown_op = op_list
    unlink_op(noop)
    assert len(start_op.exe_deps) == 0
    assert len(start_op.deps_of) == 1
    assert start_op.deps_of[0] == shutdown_op
    assert len(shutdown_op.exe_deps) == 1
    assert shutdown_op.exe_deps[0] == start_op
    assert len(shutdown_op.deps_of) == 0


def test_unlink_op_end():
    op_list = get_three_ops_fixture()
    start_op, noop, shutdown_op = op_list
    unlink_op(shutdown_op)
    assert len(start_op.exe_deps) == 0
    assert len(start_op.deps_of) == 1
    assert start_op.deps_of[0] == noop
    assert len(noop.exe_deps) == 1
    assert noop.exe_deps[0] == start_op
    assert len(noop.deps_of) == 0


def test_unlink_op_multiple():
    _, _, base1 = get_noop_fixture("//:base1")
    _, _, base2 = get_noop_fixture("//:base2")
    _, _, base3 = get_noop_fixture("//:base3")
    _, _, middle = get_noop_fixture("//:middle")
    _, _, end = get_noop_fixture("//:end")

    middle.add_exe_dep(base1)
    middle.add_exe_dep(base2)
    middle.add_exe_dep(base3)
    base1.add_dep_of(middle)
    base2.add_dep_of(middle)
    base3.add_dep_of(middle)
    end.add_exe_dep(middle)
    middle.add_dep_of(end)

    assert len(end.exe_deps) == 1
    assert end.exe_deps[0] == middle
    assert len(end.deps_of) == 0
    assert len(middle.exe_deps) == 3
    assert len(middle.deps_of) == 1

    unlink_op(middle)

    assert len(end.exe_deps) == 3
    assert base1 in end.exe_deps
    assert base2 in end.exe_deps
    assert base3 in end.exe_deps
    assert len(base1.deps_of) == 1
    assert base1.deps_of[0] == end
    assert len(base2.deps_of) == 1
    assert base2.deps_of[0] == end
    assert len(base3.deps_of) == 1
    assert base3.deps_of[0] == end


def get_noop_fixture(id_str: str) -> Tuple[TaskIdentifier, TaskType, NoOp]:
    task_id = TaskIdentifier.from_str(id_str)
    task = Group(identifier=task_id, cond_file_path=pathlib.Path("."), deps=[])
    op = NoOp(initial_state=OperationState.QUEUED, identifier=task_id, task=task)
    return task_id, task, op


def get_three_ops_fixture() -> List[Operation]:
    start_op = StartRemoteEnv(
        initial_state=OperationState.QUEUED,
        env_name="test",
        start_runnable=None,
        working_path=pathlib.Path("."),
        connect_config_runnable="",
    )
    shutdown_op = ShutdownRemoteEnv(
        initial_state=OperationState.QUEUED,
        env_name="test",
        shutdown_runnable=None,
        working_path=pathlib.Path("."),
    )
    _, _, op = get_noop_fixture("//:task1")
    op_list = [start_op, op, shutdown_op]
    _link_ops(op_list)

    # Initial state checks.
    assert len(start_op.exe_deps) == 0
    assert len(start_op.deps_of) == 1
    assert start_op.deps_of[0] == op

    assert len(op.exe_deps) == 1
    assert op.exe_deps[0] == start_op
    assert len(op.deps_of) == 1
    assert op.deps_of[0] == shutdown_op

    assert len(shutdown_op.exe_deps) == 1
    assert shutdown_op.exe_deps[0] == op
    assert len(shutdown_op.deps_of) == 0

    return op_list


def _link_ops(ops: List[Operation]) -> None:
    """
    Links operations together based on dependencies.
    """
    for idx, op in enumerate(ops):
        if idx == 0:
            continue
        prev_op = ops[idx - 1]
        prev_op.add_dep_of(op)
        op.add_exe_dep(prev_op)
