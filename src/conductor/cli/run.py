from conductor.context import Context
from conductor.task_identifier import TaskIdentifier
from conductor.execution.plan import ExecutionPlan
from conductor.utils.user_code import cli_command


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
    parser.set_defaults(func=main)


@cli_command
def main(args):
    ctx = Context.from_cwd()
    task_identifier = TaskIdentifier.from_str(
        args.task_identifier,
        require_prefix=False,
    )
    ctx.task_index.load_transitive_closure(task_identifier)
    plan = ExecutionPlan(task_identifier, run_again=args.again)
    plan.execute(ctx)
