import itertools
from typing import Tuple, List, Set, Dict, Optional

from conductor.execution.operation_state import OperationState
from conductor.execution.ops.operation import Operation
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.transfer_repo import TransferRepo
from conductor.execution.optim_rules.rule import OptimizerRule
from conductor.execution.optim_rules.utils import (
    traverse_op_dag,
    traverse_up_op_dag,
    unlink_op,
)
from conductor.execution.plan import ExecutionPlan


class JoinSiblingEnvs(OptimizerRule):
    """
    Looks for situations where we have

      StartRemoteEnv -> (ops) -> ShutdownRemoteEnv -\
      StartRemoteEnv -> (ops) -> ShutdownRemoteEnv -+--- -> (other ops)
      ...                                           |
      StartRemoteEnv -> (ops) -> ShutdownRemoteEnv -/

    and joins the sibling StartRemoteEnv and ShutdownRemoteEnv operations into a
    single start/stop pair.
    """

    def name(self) -> str:
        return "JoinSiblingEnvs"

    def apply(self, plan: ExecutionPlan) -> Tuple[bool, ExecutionPlan]:
        if plan.root_op is None:
            return False, plan

        # 1. Find all ShutdownRemoteEnv operations
        shutdown_ops = self._find_shutdown_env_ops(plan.root_op)

        if len(shutdown_ops) <= 1:
            # Simple case: No merging is possible.
            return False, plan

        # 2. Group into environments.
        env_map: Dict[str, List[Operation]] = {}
        for op in shutdown_ops:
            try:
                env_map[op.env_name].append(op)
            except KeyError:
                env_map[op.env_name] = [op]

        id_map = {id(op): op for op in plan.all_ops}
        overall_groupings = []

        for env_name, env_ops in env_map.items():
            if len(env_ops) <= 1:
                # No merging is possible for this environment.
                continue

            # 3. Compute common ancestors for each ShutdownRemoteEnv operation.
            reachable = [
                (shutdown_op, self._find_reachable_ops(shutdown_op))
                for shutdown_op in env_ops
            ]

            # 4. Greedily form groups based on the closest common ancestor.
            groupings = self._find_groupings(reachable, id_map)
            if len(groupings) == 0:
                continue
            overall_groupings.append((env_name, groupings))

        if len(overall_groupings) == 0:
            return False, plan

        # 5. Merge the groups.
        for env_name, groupings in overall_groupings:
            for group in groupings:
                ops_in_group, common_ancestor = group
                start_ops: List[StartRemoteEnv] = []

                invalid_group = False
                for op in ops_in_group:  # type: ignore
                    closest_starts = self._find_closest_start_ops(op)
                    if len(closest_starts) != 1:
                        # For simplicity, we ignore the case where there are
                        # multiple closest start ops.
                        invalid_group = True
                        break
                    start_ops.append(closest_starts[0])

                if invalid_group:
                    continue

                # Merge into one start/stop pair.
                # Strategy:
                # - Create common start/end ops
                # - Link them into the graph
                # - Unlink the obsolete ops
                assert len(start_ops) > 0
                assert len(ops_in_group) > 0
                assert isinstance(ops_in_group[0], ShutdownRemoteEnv)
                common_start = start_ops[0].clone_without_deps()
                common_end = ops_in_group[0].clone_without_deps()
                xfer = TransferRepo(
                    initial_state=OperationState.QUEUED, env_name=env_name
                )
                xfer.add_exe_dep(common_start)
                common_start.add_dep_of(xfer)

                # Link the common start op to just before all the start ops.
                for start_op in start_ops:
                    # Remove the start op's dependencies.
                    for dep in start_op.exe_deps:
                        dep.deps_of.remove(start_op)
                    # Add the deps to the common start op.
                    for dep in start_op.exe_deps:
                        common_start.add_exe_dep(dep)
                        dep.add_dep_of(common_start)

                    # Place the xfer op just before the start op.
                    start_op.exe_deps.clear()
                    xfer.add_dep_of(start_op)
                    start_op.add_exe_dep(xfer)

                # Link the common end op to just after all the end ops. Also
                # make it a dependency on the common ancestor.
                for end_op in ops_in_group:
                    end_op.add_dep_of(common_end)
                    common_end.add_exe_dep(end_op)

                common_end.add_dep_of(common_ancestor)
                common_ancestor.add_exe_dep(common_end)

                # Unlink the obsolete ops.
                for op in itertools.chain(start_ops, ops_in_group):  # type: ignore
                    unlink_op(op)
                    plan.all_ops.remove(op)
                    try:
                        plan.initial_ops.remove(op)
                    except ValueError:
                        pass

                plan.all_ops.append(common_start)
                plan.all_ops.append(common_end)
                plan.all_ops.append(xfer)

                if len(common_start.exe_deps) == 0:
                    plan.initial_ops.append(common_start)

        return True, plan

    def _find_shutdown_env_ops(self, root_op: Operation) -> List[ShutdownRemoteEnv]:
        shutdown_ops: List[ShutdownRemoteEnv] = []

        def visitor(op: Operation) -> None:
            nonlocal shutdown_ops
            if isinstance(op, ShutdownRemoteEnv):
                shutdown_ops.append(op)

        traverse_op_dag(root_op, visitor)
        return shutdown_ops

    def _find_reachable_ops(self, root_op: Operation) -> List[Operation]:
        reachable_ops: List[Operation] = []

        def visitor(op: Operation) -> None:
            nonlocal reachable_ops
            reachable_ops.append(op)

        traverse_up_op_dag(root_op, visitor)
        return reachable_ops

    def _find_groupings(
        self,
        candidates: List[Tuple[Operation, List[Operation]]],
        id_map: Dict[int, Operation],
    ) -> List[Tuple[List[Operation], Operation]]:
        # We create groupings based on the closest common ancestor. The
        # `candidates` list contains a list of operations reachable from each
        # shutdown op. We take the largest common set of reachable operations --
        # this corresponds to the closest common ancestor. We find the largest
        # intersection among two shutdown operations. Then we try to expand it
        # from the remaining candidates to form a group. We repeat until there
        # are no more groupings left.
        candidate_sets = [
            (id(op), set([id(rop) for rop in reachable]), reachable)
            for op, reachable in candidates
        ]
        groups: List[Tuple[List[Operation], Operation]] = []

        while len(candidate_sets) > 0:
            result = self._find_best_pair(candidate_sets)
            if result is None:
                return groups

            pair, common_set, common_ancestor = result
            additional_ops = []

            remaining_candidates = []

            for op_id, reachable_set, reachable_ops in candidate_sets:
                if op_id in pair:
                    continue

                if len(reachable_set.intersection(common_set)) == len(common_set):
                    # Observe that the intersection can only decrease in size;
                    # thus if the intersection is the same size, we must have
                    # the same set of ancestors.
                    additional_ops.append(op_id)
                else:
                    remaining_candidates.append((op_id, reachable_set, reachable_ops))

            ops_in_group = [id_map[op_id] for op_id in pair]
            for op_id in additional_ops:
                ops_in_group.append(id_map[op_id])

            groups.append((ops_in_group, common_ancestor))
            candidate_sets = remaining_candidates

        return groups

    def _find_best_pair(
        self, candidate_sets: List[Tuple[int, Set[int], List[Operation]]]
    ) -> Optional[Tuple[List[int], Set[int], Operation]]:
        best_so_far = None
        best_so_far_len = 0
        best_so_far_set = None
        best_ancestor = None

        for op_id, reachable_set, reachable_ops in candidate_sets:
            for rop_id, rop_reachable_set, _ in candidate_sets:
                if op_id == rop_id:
                    continue

                # If we have [start, shutdown] --> [start, shutdown] -> other op
                # then the two groups will have a common ancestor. But we do not
                # want this case. We can detect these occurrences by checking
                # for subset relationships in the reachable set.
                if reachable_set.issubset(
                    rop_reachable_set
                ) or rop_reachable_set.issubset(reachable_set):
                    continue

                common = reachable_set.intersection(rop_reachable_set)
                if len(common) > best_so_far_len:
                    best_so_far = [op_id, rop_id]
                    best_so_far_len = len(common)
                    best_so_far_set = common
                    # Ops are ordered in distance away. We want the closest
                    # common ancestor.
                    for op in reachable_ops:
                        if id(op) in common:
                            best_ancestor = op
                            break
                    assert best_ancestor in reachable_ops

        if best_so_far is None:
            # No common ancestors. In Conductor, this should not happen because
            # there will always be a root operation.
            return None

        assert best_so_far_set is not None
        assert best_ancestor is not None
        assert best_so_far_len == len(best_so_far_set)
        return best_so_far, best_so_far_set, best_ancestor

    def _find_closest_start_ops(
        self, shutdown_op: ShutdownRemoteEnv
    ) -> List[StartRemoteEnv]:
        start_ops: List[StartRemoteEnv] = []
        env_name = shutdown_op.env_name

        stack: List[Operation] = [shutdown_op]
        visited: Set[int] = set()

        while len(stack) > 0:
            op = stack.pop()
            if id(op) in visited:
                continue

            visited.add(id(op))
            if isinstance(op, StartRemoteEnv) and op.env_name == env_name:
                start_ops.append(op)
            else:
                stack.extend(op.exe_deps)

        return start_ops
