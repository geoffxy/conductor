import multiprocessing

from conductor.context import Context
from conductor.errors import InvalidJobsCount, CannotSelectJobCount
from conductor.task_identifier import TaskIdentifier
from conductor.execution.executor import Executor
from conductor.execution.plan import ExecutionPlan
from conductor.utils.user_code import cli_command


# Value used to indicate when Conductor should select the maximum number of
# parallel tasks.
_AUTOFILL_JOBS = -1


def register_command(subparsers):
    parser = subparsers.add_parser(
        "run",
        help="Run a specific Conductor task.",
    )
    parser.add_argument(
        "task_identifier",
        type=str,
        help="The task that Conductor should run.",
    )
    parser.add_argument(
        "-a",
        "--again",
        action="store_true",
        help="Run all the relevant tasks again. Conductor by default will use cached "
        "results for certain tasks, if they exist. Setting this flag will make "
        "Conductor run all the relevant tasks again, regardless of the cache.",
    )
    parser.add_argument(
        "-e",
        "--stop-early",
        action="store_true",
        help="Stop executing a task if any dependent task fails. By default, "
        "if a dependent task fails, Conductor will still try to execute the "
        "rest of the task's dependencies that do not depend on the failed "
        "task.",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        nargs="?",
        const=_AUTOFILL_JOBS,
        default=None,
        help="The maximum number of tasks that Conductor can run in parallel. "
        "If this flag is used without specifying a value, Conductor will set "
        "this number to be the number of virtual CPUs detected in this machine.",
    )
    parser.set_defaults(func=main)


def validate_and_retrieve_jobs_count(args) -> int:
    if args.jobs is None:
        return 1
    elif args.jobs == _AUTOFILL_JOBS:
        try:
            return multiprocessing.cpu_count()
        except ValueError as ex:
            raise CannotSelectJobCount() from ex
    else:
        assert args.jobs is not None
        if args.jobs <= 0:
            raise InvalidJobsCount()
        return args.jobs


@cli_command
def main(args):
    num_jobs = validate_and_retrieve_jobs_count(args)
    ctx = Context.from_cwd()
    task_identifier = TaskIdentifier.from_str(
        args.task_identifier,
        require_prefix=False,
    )
    ctx.task_index.load_transitive_closure(task_identifier)
    plan = ExecutionPlan.for_task(task_identifier, ctx, run_again=args.again)
    executor = Executor(execution_slots=num_jobs)
    executor.run_plan(plan, ctx, stop_on_first_error=args.stop_early)
