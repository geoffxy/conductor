import pathlib

from conductor.context import Context
from conductor.errors import ArchiveFileInvalid
from conductor.utils.user_code import cli_command
from conductor.utils.output_archiving import restore_archive


def register_command(subparsers):
    parser = subparsers.add_parser(
        "restore",
        help="Restore previously archived task outputs.",
    )
    parser.add_argument(
        "archive_file",
        type=str,
        help="Path to the archive file to restore.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="If set, the restore operation will fail if any task output is already present.",
    )
    parser.set_defaults(func=main)


@cli_command
def main(args):
    ctx = Context.from_cwd()

    archive_file = pathlib.Path(args.archive_file)
    if not archive_file.is_file():
        raise ArchiveFileInvalid()

    restore_archive(ctx, archive_file, expect_no_duplicates=args.strict)
