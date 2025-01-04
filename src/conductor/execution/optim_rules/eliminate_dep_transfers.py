from typing import Tuple, Dict, List, Set, NamedTuple

from conductor.execution.ops.operation import Operation
from conductor.execution.ops.run_remote_task import RunRemoteTask
from conductor.execution.ops.shutdown_remote_env import ShutdownRemoteEnv
from conductor.execution.ops.start_remote_env import StartRemoteEnv
from conductor.execution.ops.transfer_results import TransferResults, TransferDirection
from conductor.execution.optim_rules.rule import OptimizerRule
from conductor.execution.optim_rules.utils import unlink_op
from conductor.execution.plan import ExecutionPlan
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier


class EliminateDepTransfers(OptimizerRule):
    """
    Removes unneeded TransferResults operations. This is useful when a task's
    dependency has already executed in the same remote environment.
    """

    def name(self) -> str:
        return "EliminateTransferRepos"

    def apply(self, plan: ExecutionPlan) -> Tuple[bool, ExecutionPlan]:
        ops_to_remove = []
        made_changes = False

        for initial_op in plan.initial_ops:
            # The dict stores the active environments and the results that are
            # already available in the remote environment.
            stack: List[Tuple[Operation, Dict[str, _ExistingResults]]] = [
                (initial_op, {})
            ]
            # N.B. The task graph is a DAG. We do not track visited nodes
            # because we need to traverse all possible paths.
            while len(stack) > 0:
                try:
                    op, env_results = stack.pop()

                    next_env_results = self._clone_env_results(env_results)
                    if isinstance(op, StartRemoteEnv):
                        next_env_results[op.env_name] = _ExistingResults()

                    elif isinstance(op, ShutdownRemoteEnv):
                        del next_env_results[op.env_name]

                    elif isinstance(op, TransferResults):
                        rr = next_env_results[op.env_name].reconcile_transfer_op(op)
                        for versioned_to_remove in rr.versioned:
                            op.versioned_tasks.remove(versioned_to_remove)
                        for unversioned_to_remove in rr.unversioned:
                            op.unversioned_tasks.remove(unversioned_to_remove)
                        if (
                            len(op.versioned_tasks) == 0
                            and len(op.unversioned_tasks) == 0
                        ):
                            ops_to_remove.append(op)
                        if len(rr.versioned) > 0 or len(rr.unversioned) > 0:
                            made_changes = True

                    elif isinstance(op, RunRemoteTask):
                        next_env_results[op.env_name].reconcile_run(op)

                    for next_op in op.deps_of:
                        stack.append((next_op, next_env_results))
                except KeyError:
                    # This happens if we are on a path that was originally not
                    # in an environment but has joined a path that is now in an
                    # environment. In this case, we skip the path.
                    pass

        if len(ops_to_remove) == 0:
            return made_changes, plan

        for remove in ops_to_remove:
            unlink_op(remove)
            plan.all_ops.remove(remove)
            try:
                # Generally, `TransferResults` will not be an initial op.
                plan.initial_ops.remove(remove)
            except ValueError:
                pass

        return True, plan

    def _clone_env_results(
        self, env_results: Dict[str, "_ExistingResults"]
    ) -> Dict[str, "_ExistingResults"]:
        new_env_results = {}
        for env_name, results in env_results.items():
            new_env_results[env_name] = results.clone()
        return new_env_results


class _RedundantTransfer(NamedTuple):
    versioned: List[Tuple[TaskIdentifier, Version]]
    unversioned: List[TaskIdentifier]


class _ExistingResults:
    def __init__(self) -> None:
        self._versioned: Set[Tuple[TaskIdentifier, Version]] = set()
        self._unversioned: Set[TaskIdentifier] = set()

    def reconcile_transfer_op(self, op: TransferResults) -> _RedundantTransfer:
        versioned: List[Tuple[TaskIdentifier, Version]] = []
        unversioned: List[TaskIdentifier] = []

        if op.direction == TransferDirection.FromEnv:
            # Nothing to do for transfers from the remote environment.
            return _RedundantTransfer(versioned, unversioned)

        for versioned_task in op.versioned_tasks:
            if versioned_task in self._versioned:
                versioned.append(versioned_task)
            else:
                self._versioned.add(versioned_task)

        for unversioned_task in op.unversioned_tasks:
            if unversioned_task in self._unversioned:
                unversioned.append(unversioned_task)
            else:
                self._unversioned.add(unversioned_task)

        return _RedundantTransfer(versioned, unversioned)

    def reconcile_run(self, op: RunRemoteTask) -> None:
        assert op.main_task is not None
        task_id = op.main_task.identifier
        if op.output_version is not None:
            self._versioned.add((task_id, op.output_version))
        else:
            self._unversioned.add(task_id)

    def clone(self) -> "_ExistingResults":
        new = _ExistingResults()
        new._versioned = self._versioned.copy()  # pylint: disable=protected-access
        new._unversioned = self._unversioned.copy()  # pylint: disable=protected-access
        return new
