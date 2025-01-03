from typing import Tuple

from conductor.execution.plan import ExecutionPlan


class OptimizerRule:
    """
    Represents an optimization rule that can be applied to an execution plan.
    """

    def name(self) -> str:
        """
        Returns the name of the rule.
        """
        raise NotImplementedError

    def apply(self, plan: ExecutionPlan) -> Tuple[bool, ExecutionPlan]:
        """
        Attempt to apply this rule to the given plan. Returns a tuple of whether
        or not the rule modified the plan and the modified (or original) plan.
        """
        raise NotImplementedError
