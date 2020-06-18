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
