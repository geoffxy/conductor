import multiprocessing
import sys

from conductor.context import Context
from conductor.errors import (
    InvalidJobsCount,
    CannotSelectJobCount,
    CannotSetAgainAndCommit,
    CommitFlagUnsupported,
    InvalidCommitSymbol,
    CannotSetBothCommitFlags,
    AtLeastCommitNotAncestor,
)
from conductor.task_identifier import TaskIdentifier
from conductor.execution.executor import Executor
from conductor.execution.plan import ExecutionPlan
from conductor.utils.user_code import cli_command
from conductor.utils.colored_output import print_bold


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
        "-c",
        "--at-least",
        metavar="COMMIT",
        type=str,
        help="Run all relevant tasks that have not yet run against a commit that is "
        "at least as new as the specified commit. You can specify a commit using a "
        "hash, branch name, or tag. Conductor by default uses cached results for "
        "certain tasks, if they exist. Setting this flag will make Conductor run "
        "all relevant tasks that do not have cached entries for the current commit. "
        "This flag cannot be used if your project is not managed by Git, or if "
        "Conductor's Git integration was disabled.",
    )
    parser.add_argument(
        "--this-commit",
        action="store_true",
        help="Run all relevant tasks that have not yet run against the current "
        "commit. Equivalent to setting --at-least=HEAD.",
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
    parser.add_argument(
        "--check",
        action="store_true",
        help="When set, Conductor will parse and validate all tasks that would be "
        "executed but it will not actually execute the tasks. This flag is useful "
        "for checking that tasks are defined correctly in COND files.",
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


def validate_args(args, ctx: Context):
    for_commit = args.this_commit or args.at_least is not None
    if args.this_commit and args.at_least is not None:
        raise CannotSetBothCommitFlags()
    if args.again and for_commit:
        raise CannotSetAgainAndCommit()
    if for_commit and not ctx.uses_git:
        raise CommitFlagUnsupported()
    if for_commit and ctx.current_commit is None:
        raise CommitFlagUnsupported()


@cli_command
def main(args):
    num_jobs = validate_and_retrieve_jobs_count(args)
    ctx = Context.from_cwd()
    validate_args(args, ctx)
    task_identifier = TaskIdentifier.from_str(
        args.task_identifier,
        require_prefix=False,
    )
    ctx.task_index.load_transitive_closure(task_identifier)

    if args.check:
        print_bold(
            "✓ Task(s) are OK. Skipping execution because --check was set.",
            file=sys.stderr,
        )
        return

    # Convert the specified commit to a hash, if needed.
    commit = None
    if args.this_commit or args.at_least is not None:
        parsed_commit = ctx.git.rev_parse(
            args.at_least if args.at_least is not None else "HEAD"
        )
        if parsed_commit is None:
            raise InvalidCommitSymbol(symbol=args.at_least)
        commit = parsed_commit

        # Validate the commit hash. It must be an ancestor of the current commit.
        assert ctx.current_commit is not None
        commit_is_ancestor = ctx.git.is_ancestor(ctx.current_commit.hash, commit)
        if not commit_is_ancestor:
            raise AtLeastCommitNotAncestor()

    plan = ExecutionPlan.for_task(
        task_identifier, ctx, run_again=args.again, at_least_commit=commit
    )
    executor = Executor(execution_slots=num_jobs)
    executor.run_plan(plan, ctx, stop_on_first_error=args.stop_early)
