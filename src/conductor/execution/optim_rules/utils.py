from typing import Callable, Set

from conductor.execution.ops.operation import Operation
from conductor.execution.plan import ExecutionPlan


def unlink_op(op: Operation) -> None:
    """
    Removes this operation from its containing graph.
    """

    # Our dependencies
    exe_deps = op.exe_deps
    # Tasks that depend on us
    deps_of = op.deps_of

    for dep in exe_deps:
        dep.deps_of.remove(op)

    for dep_of in deps_of:
        dep_of.exe_deps.remove(op)

    # Tasks that depend on us now have our dependencies.
    for dep_of in deps_of:
        for dep in exe_deps:
            dep_of.add_exe_dep(dep)

    # Our dependencies are now forwarded to our deps_of
    for dep in exe_deps:
        for dep_of in deps_of:
            dep.add_dep_of(dep_of)


def traverse_plan(plan: ExecutionPlan, visitor: Callable[[Operation], None]) -> None:
    if plan.root_op is None:
        return
    traverse_op_dag(plan.root_op, visitor)


def traverse_op_dag(root_op: Operation, visitor: Callable[[Operation], None]) -> None:
    stack = [root_op]
    visited: Set[int] = set()

    while len(stack) > 0:
        op = stack.pop()
        if id(op) in visited:
            continue

        visited.add(id(op))
        visitor(op)

        stack.extend(op.exe_deps)


def traverse_up_op_dag(
    root_op: Operation, visitor: Callable[[Operation], None]
) -> None:
    """
    Similar to traverse_op_dag, but traverses the graph upwards (towards
    operations that depend on the given operation).
    """

    stack = [root_op]
    visited: Set[int] = set()

    while len(stack) > 0:
        op = stack.pop()
        if id(op) in visited:
            continue

        visited.add(id(op))
        visitor(op)

        stack.extend(op.deps_of)
