

def register_command(subparsers):
    parser = subparsers.add_parser(
        "run",
        help="Run a specific Conductor target.",
    )
    parser.add_argument("target", help="The target that Conductor should run.")
    parser.set_defaults(func=main)


def main(args):
    pass
