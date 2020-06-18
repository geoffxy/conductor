import argparse
import sys

import conductor
import conductor.cli.run


def main():
    parser = argparse.ArgumentParser(
        description="Conductor: A simple, elegant, and opinionated tool that "
                    "orchestrates your research computing.",
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Print conductor's version and exit.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode (used mainly during Conductor development).",
    )
    subparsers = parser.add_subparsers(title="Commands")
    conductor.cli.run.register_command(subparsers)
    args = parser.parse_args()

    if args.version:
        print(conductor.__version__)
        return

    if "func" not in args:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
