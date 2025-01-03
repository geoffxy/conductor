from typing import Tuple, List, Set, Dict

from conductor.execution.ops.operation import Operation
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.optim_rules.rule import OptimizerRule
from conductor.execution.plan import ExecutionPlan
from conductor.execution.ops.run_remote_task import RunRemoteTask
from conductor.execution.ops.run_task_executable import RunTaskExecutable
from conductor.execution.optim_rules.utils import unlink_op


class EliminateShutdownStartEnv(OptimizerRule):
    """
    Looks for situations where we have

    (other op) -> ShutdownRemoteEnv -> (trivial ops) -> StartRemoteEnv -> (other op)

    and eliminates the ShutdownRemoteEnv and StartRemoteEnv operations if they
    are for the same environment.
    """

    def name(self) -> str:
        return "EliminateShutdownStartEnv"

    def apply(self, plan: ExecutionPlan) -> Tuple[bool, ExecutionPlan]:
        if plan.root_op is None:
            return False, plan

        # 1. Find all StartEnv ops.
        start_ops = self._find_start_env_ops(plan.root_op)

        # 2. For each StartEnv op, find the corresponding ShutdownEnv op(s).
        matching_starts: Dict[int, _Pair] = {}
        for start_op in start_ops:
            shutdown_ops = self._find_closest_shutdown_ops(start_op)

            # This happens when we are examining the StartEnv op in the plan.
            if len(shutdown_ops) == 0:
                continue

            # For simplicity, we skip the case where there are multiple
            # ShutdownEnv ops. This happens when there are multiple branches
            # each with a shutdown that then lead to this start op.
            if len(shutdown_ops) > 1:
                continue

            # Keep track of the number of shutdown op occurrences. If they occur
            # more than once, it means that the op maps to multiple start ops,
            # which is another case we ignore for simplicity.
            shutdown_op = shutdown_ops[0]
            try:
                matching_starts[id(shutdown_op)].shutdown_occurrences += 1
            except KeyError:
                matching_starts[id(shutdown_op)] = _Pair(start_op, shutdown_op)

        pairs_to_remove = [
            pair
            for pair in matching_starts.values()
            if pair.shutdown_occurrences == 1 and pair.is_trivial()
        ]

        if len(pairs_to_remove) == 0:
            return False, plan

        for pair in pairs_to_remove:
            # Unlink the ops from the graph.
            unlink_op(pair.shutdown_op)
            unlink_op(pair.start_op)
            plan.all_ops.remove(pair.shutdown_op)
            plan.all_ops.remove(pair.start_op)

        return True, plan

    def _find_start_env_ops(self, root_op: Operation) -> List[StartRemoteEnv]:
        start_ops: List[StartRemoteEnv] = []

        stack = [root_op]
        visited: Set[int] = set()

        while len(stack) > 0:
            op = stack.pop()
            if id(op) in visited:
                continue

            visited.add(id(op))
            if isinstance(op, StartRemoteEnv):
                start_ops.append(op)

            stack.extend(op.exe_deps)

        return start_ops

    def _find_closest_shutdown_ops(
        self, start_op: StartRemoteEnv
    ) -> List[ShutdownRemoteEnv]:
        shutdown_ops: List[ShutdownRemoteEnv] = []
        env_name = start_op.env_name

        stack: List[Operation] = [start_op]
        visited: Set[int] = set()

        while len(stack) > 0:
            op = stack.pop()
            if id(op) in visited:
                continue

            visited.add(id(op))
            if isinstance(op, ShutdownRemoteEnv) and op.env_name == env_name:
                shutdown_ops.append(op)
            else:
                stack.extend(op.exe_deps)

        return shutdown_ops


class _Pair:
    def __init__(self, start_op: StartRemoteEnv, shutdown_op: ShutdownRemoteEnv):
        self.shutdown_op = shutdown_op
        self.start_op = start_op
        self.shutdown_occurrences = 1

    def is_trivial(self) -> bool:
        # This is based on heuristics.
        # - If we have Shutdown -> Start.
        # - If the operations between Shutdown and Start are "fast" operations.
        try:
            self.start_op.exe_deps.index(self.shutdown_op)
            return True
        except ValueError:
            # This means that the shutdown op is not a direct dependency of the
            # start op.
            pass

        # Find all paths between start and shutdown and check that they are all
        # "trivial".
        stack: List[Tuple[Operation, int]] = [(self.start_op, 0)]
        curr_path: List[Operation] = []

        while len(stack) > 0:
            op, visit_count = stack.pop()

            if visit_count == 0:
                if op == self.shutdown_op:
                    assert len(curr_path) > 0
                    if not self._is_path_trivial(curr_path[1:]):
                        return False
                else:
                    curr_path.append(op)
                    stack.append((op, 1))
                    stack.extend((dep, 0) for dep in op.exe_deps)
            else:
                curr_path.pop()

        return True

    def _is_path_trivial(self, path: List[Operation]) -> bool:
        for op in path:
            # Heuristic: These operations are likely to take a long time.
            if isinstance(op, (RunRemoteTask, RunTaskExecutable)):
                return False
        return True
