from typing import Tuple, List

from conductor.execution.optim_rules.rule import OptimizerRule
from conductor.execution.optim_rules.eliminate_shutdown_start_env import (
    EliminateShutdownStartEnv,
)
from conductor.execution.optim_rules.eliminate_transfer_repos import (
    EliminateTransferRepos,
)
from conductor.execution.optim_rules.join_sibling_envs import JoinSiblingEnvs
from conductor.execution.plan import ExecutionPlan


class ExecutionPlanOptimizer:
    @classmethod
    def with_default_rules(cls) -> "ExecutionPlanOptimizer":
        return cls(
            [
                JoinSiblingEnvs(),
                EliminateTransferRepos(),
                EliminateShutdownStartEnv(),
            ]
        )

    def __init__(self, rules: List[OptimizerRule]) -> None:
        self._rules = rules

    def optimize(
        self, plan: ExecutionPlan, max_passes: int = 100
    ) -> Tuple[ExecutionPlan, int]:
        """
        Optimizes the given execution plan using the rules in this optimizer.
        Returns the optimized plan and the number of passes it took to reach the
        optimized plan.
        """
        curr_plan = plan
        for pass_idx in range(max_passes):
            has_changed_this_pass = False
            for rule in self._rules:
                changed, curr_plan = rule.apply(curr_plan)
                has_changed_this_pass = has_changed_this_pass or changed

            if not has_changed_this_pass:
                return curr_plan, pass_idx + 1

        return curr_plan, max_passes
