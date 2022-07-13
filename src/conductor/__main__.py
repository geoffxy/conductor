import argparse
import sys

import conductor
import conductor.cli.run
import conductor.cli.archive
import conductor.cli.restore
import conductor.cli.where
import conductor.cli.clean
import conductor.cli.gc


def main():
    parser = argparse.ArgumentParser(
        description="Conductor: A simple and elegant research computing orchestrator.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print Conductor's version and exit.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode (used mainly during Conductor development).",
    )
    subparsers = parser.add_subparsers(title="Commands")
    conductor.cli.run.register_command(subparsers)
    conductor.cli.archive.register_command(subparsers)
    conductor.cli.restore.register_command(subparsers)
    conductor.cli.where.register_command(subparsers)
    conductor.cli.clean.register_command(subparsers)
    conductor.cli.gc.register_command(subparsers)
    args = parser.parse_args()

    if args.version:
        print("Conductor", conductor.__version__)
        return

    if "func" not in args:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
