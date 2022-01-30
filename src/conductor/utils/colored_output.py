from typing import Dict


class _Colors:
    Blue = "\033[34m"
    Cyan = "\033[36m"
    Green = "\033[32m"
    Red = "\033[31m"
    Yellow = "\033[33m"

    Bold = "\033[1m"
    Reset = "\033[0m"


def print_cyan(message: str, **kwargs) -> None:
    _print_colored(message, _Colors.Cyan, kwargs)


def print_blue(message: str, **kwargs) -> None:
    _print_colored(message, _Colors.Blue, kwargs)


def print_green(message: str, **kwargs) -> None:
    _print_colored(message, _Colors.Green, kwargs)


def print_red(message: str, **kwargs) -> None:
    _print_colored(message, _Colors.Red, kwargs)


def print_yellow(message: str, **kwargs) -> None:
    _print_colored(message, _Colors.Yellow, kwargs)


def print_bold(message: str, **kwargs) -> None:
    _print_colored(message, _Colors.Bold, kwargs)


def _print_colored(message: str, color: str, kwargs: Dict) -> None:
    if "bold" in kwargs:
        if kwargs["bold"]:
            color += _Colors.Bold
        del kwargs["bold"]
    print(f"{color}{message}{_Colors.Reset}", **kwargs)
