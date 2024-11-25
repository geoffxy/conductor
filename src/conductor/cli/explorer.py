from conductor.explorer.explorer import start_explorer
from conductor.utils.user_code import cli_command
from conductor.errors import ConductorAbort


def register_command(subparsers):
    parser = subparsers.add_parser(
        "explorer",
        help="Launch Conductor's web-based result version explorer.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="The host to bind to when serving the explorer.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="The port to listen on when serving the explorer.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="If set, do not automatically start the web browser.",
    )
    parser.set_defaults(func=main)


@cli_command
def main(args):
    try:
        start_explorer(
            host=args.host, port=args.port, launch_browser=not args.no_browser
        )
    except ConductorAbort:
        # We ignore this exception because it is raised when the user hits
        # Ctrl+C to shut down the server.
        pass
