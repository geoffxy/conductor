import pathlib
import importlib.resources as pkg_resources

from fabric.connection import Connection

import conductor
import conductor.envs.resources as env_resources
from conductor.config import (
    MAESTRO_PYTHON_VERSION,
    MAESTRO_COND_WHEEL_TEMPLATE,
    MAESTRO_VENV_NAME,
)
from conductor.errors import MaestroInstallError


def ensure_maestro_installed(c: Connection, maestro_root: pathlib.Path) -> None:
    """
    Ensures that Maestro is installed in the remote environment connected to by
    the connection `c`.
    """

    # General strategy:
    # - Keep all Maestro-related code under a special root directory, specified
    #   using `MAESTRO_ROOT`. The assumption is that `MAESTRO_ROOT` is stored
    #   under `$HOME` (we assume a Unix-like remote environment).
    # - Rely on `pyenv` to install a compatible version of Python in the remote
    #   environment. Note that `pyenv` depends on `git`.
    # - Copy the entire Conductor module into the remote environment and install
    #   its dependencies in the pyenv.
    #
    # Design goals:
    # - We should make this install as seamless as possible, similar to how easy
    #   it is to install VSCode server.
    # - OK to assume a Unix-like remote environment. Should ideally make sure
    #   this works in a generic EC2 environment and inside a Docker container.

    try:
        installer = _MaestroInstaller(c, maestro_root)
        installer.ensure_root_dir()
        installer.ensure_pyenv_installed()
        installer.install_python()
        installer.ensure_virtualenv()
        installer.install_conductor_wheel()
    except Exception as ex:
        raise MaestroInstallError(error_message=str(ex)) from ex


class _MaestroInstaller:
    def __init__(self, c: Connection, maestro_root: pathlib.Path) -> None:
        self._c = c
        # This is an absolute path in the remote environment.
        self._maestro_root = maestro_root
        self._pyenv_root = self._maestro_root / "pyenv"
        self._pyenv_env = {
            "PYENV_ROOT": str(self._pyenv_root),
            "PYENV_VERSION": MAESTRO_PYTHON_VERSION,
        }

    def ensure_root_dir(self) -> None:
        self._c.run(f"mkdir -p {str(self._maestro_root)}")

    def ensure_pyenv_installed(self) -> None:
        result = self._c.run(f"ls {str(self._pyenv_root)}", warn=True, hide="both")
        if result.ok:
            # Assume install succeeded.
            return

        try:
            # Need to install.
            install_script = pkg_resources.files(env_resources).joinpath(
                "install_pyenv.sh"
            )
            with pkg_resources.as_file(install_script) as path:
                install_script_file = self._maestro_root / "install_pyenv.sh"
                self._c.put(path, str(install_script_file))
            # We want a custom install path to avoid interfering with the existing environment.
            self._c.run(
                f"bash {str(install_script_file)}",
                env=self._pyenv_env,
                hide="both",
            )
        except Exception:
            # If the installation failed, remove the directory so that we will
            # retry next time.
            self._c.run(f"rm -r {str(self._pyenv_root)}")
            raise

    def install_python(self) -> None:
        pyenv_exec = self._pyenv_root / "bin" / "pyenv"
        result = self._c.run(
            f"{str(pyenv_exec)} versions --bare",
            hide="both",
            env=self._pyenv_env,
        )
        if result.ok and MAESTRO_PYTHON_VERSION in result.stdout:
            # Assume install succeeded.
            return
        self._c.run(
            f"{str(pyenv_exec)} install {MAESTRO_PYTHON_VERSION}",
            env=self._pyenv_env,
        )

    def ensure_virtualenv(self) -> None:
        # Check if the virtualenv already exists.
        venv_location = self._maestro_root / MAESTRO_VENV_NAME
        result = self._c.run(f"ls {str(venv_location)}", warn=True, hide="both")
        if result.ok:
            # Assume the venv exists.
            return
        pyenv_exec = self._pyenv_root / "bin" / "pyenv"
        self._c.run(
            f"{str(pyenv_exec)} exec python3 -m venv {venv_location}",
            env=self._pyenv_env,
        )

    def install_conductor_wheel(self) -> None:
        # Check if Conductor is already installed.
        venv_bin = self._maestro_root / MAESTRO_VENV_NAME / "bin"
        venv_python = venv_bin / "python3"
        result = self._c.run(
            f"{str(venv_python)} -c 'import conductor; print(conductor.__version__)'",
            warn=True,
            hide="both",
        )
        if result.ok:
            installed_version = result.stdout.strip()
            if installed_version == conductor.__version__:
                return
            # Otherwise, we need to reinstall.

        wheel_file = MAESTRO_COND_WHEEL_TEMPLATE.format(version=conductor.__version__)
        # Transfer the wheel.
        wheel = pkg_resources.files(env_resources).joinpath(wheel_file)
        wheel_path = self._maestro_root / wheel_file
        with pkg_resources.as_file(wheel) as path:
            self._c.put(path, str(wheel_path))
        # Install.
        venv_pip3 = venv_bin / "pip3"
        self._c.run(
            f"{str(venv_pip3)} install '{str(wheel_path)}[envs]'",
            hide="both",
        )
