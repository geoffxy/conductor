from typing import Tuple, Dict, List, Set

from conductor.execution.ops.operation import Operation
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.transfer_repo import TransferRepo
from conductor.execution.optim_rules.rule import OptimizerRule
from conductor.execution.optim_rules.utils import unlink_op
from conductor.execution.plan import ExecutionPlan


class EliminateTransferRepos(OptimizerRule):
    """
    Eliminates the TransferRepo operation from the execution plan when it is
    unneeded (i.e., if we have already transferred it previously in this
    environment).
    """

    def name(self) -> str:
        return "EliminateTransferRepos"

    def apply(self, plan: ExecutionPlan) -> Tuple[bool, ExecutionPlan]:
        ops_to_remove = []

        for initial_op in plan.initial_ops:
            # The dict stores the active environments and whether the repo has
            # been transferred to them. If False, then the env is active but the
            # repo has not been transferred. If True, then the env is active and
            # the repo has been transferred.
            stack: List[Tuple[Operation, Dict[str, bool]]] = [(initial_op, {})]
            visited: Set[int] = set()
            while len(stack) > 0:
                op, active_envs = stack.pop()

                if id(op) in visited:
                    continue
                visited.add(id(op))

                next_envs = active_envs.copy()
                if isinstance(op, StartRemoteEnv):
                    next_envs[op.env_name] = False
                elif isinstance(op, ShutdownRemoteEnv):
                    del next_envs[op.env_name]
                elif isinstance(op, TransferRepo):
                    if next_envs[op.env_name]:
                        ops_to_remove.append(op)
                    else:
                        next_envs[op.env_name] = True

                for next_op in op.deps_of:
                    stack.append((next_op, next_envs))

        if len(ops_to_remove) == 0:
            return False, plan

        for remove in ops_to_remove:
            unlink_op(remove)
            plan.all_ops.remove(remove)
            try:
                # Generally, `TransferRepo` will not be an initial op.
                plan.initial_ops.remove(remove)
            except ValueError:
                pass

        return True, plan
