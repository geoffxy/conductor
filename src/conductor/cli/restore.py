import pathlib
import subprocess

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
    parser.set_defaults(func=main)


def extract_archive(archive_file: pathlib.Path, staging_path: pathlib.Path):
    try:
        process = subprocess.Popen(
            ["tar", "xzf", str(archive_file), "-C", str(staging_path)],
            shell=False,
        )
        process.wait()
        if process.returncode != 0:
            raise ArchiveFileInvalid().add_extra_context(
                "The tar utility returned a non-zero error code."
            )

    except OSError as ex:
        raise ArchiveFileInvalid().add_extra_context(str(ex))


@cli_command
def main(args):
    ctx = Context.from_cwd()

    archive_file = pathlib.Path(args.archive_file)
    if not archive_file.is_file():
        raise ArchiveFileInvalid()

    restore_archive(ctx, archive_file)
