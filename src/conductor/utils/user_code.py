import contextlib
import platform
import sys
import traceback

from conductor.errors import ConductorError, UnsupportedPlatform
from conductor.errors.signal import register_signal_handlers


@contextlib.contextmanager
def prevent_module_caching():
    """
    A context manager that prevents any imported modules from being cached
    after exiting.
    """
    original_modules = sys.modules.copy()
    try:
        yield
    finally:
        newly_added = {
            module_name
            for module_name in sys.modules.keys()
            if module_name not in original_modules
        }
        for module_name in newly_added:
            del sys.modules[module_name]


def check_platform_compatibility():
    """
    Conductor only supports Linux and macOS (i.e., it does not support Windows).
    """
    system = platform.system()
    if system != "Linux" and system != "Darwin":
        raise UnsupportedPlatform()


def cli_command(main):
    """
    A decorator used for CLI command entry point methods. This decorator
    takes care of reporting errors that occur when running a command.
    """

    def command_main(args):
        try:
            check_platform_compatibility()
            register_signal_handlers()
            main(args)
        except ConductorError as ex:
            if args.debug:
                print(traceback.format_exc(), file=sys.stderr)
            print("ERROR:", ex.printable_message(), file=sys.stderr)
            sys.exit(1)

    return command_main
