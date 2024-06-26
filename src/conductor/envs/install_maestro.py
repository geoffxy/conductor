import importlib.resources as pkg_resources

from fabric.connection import Connection

import conductor.envs.resources as env_resources
from conductor.config import MAESTRO_ROOT, MAESTRO_PYTHON_VERSION
from conductor.errors import MaestroInstallError


def install_maestro(c: Connection) -> None:
    """
    Installs Maestro in the remote environment connected to by `c`.
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
        installer = _MaestroInstaller.create(c)
        installer.ensure_root_dir()
        installer.ensure_pyenv_installed()
        installer.install_python()
    except Exception as ex:
        raise MaestroInstallError(error_msg=str(ex)) from ex


class _MaestroInstaller:
    @classmethod
    def create(cls, c: Connection) -> "_MaestroInstaller":
        result = c.run("echo $HOME")
        home_dir = result.stdout.strip()
        return cls(c, home_dir)

    def __init__(self, c: Connection, home_dir: str) -> None:
        self._c = c
        # This is an absolute path in the remote environment.
        self._maestro_root = f"{home_dir}/{MAESTRO_ROOT}"
        self._pyenv_root = f"{self._maestro_root}/pyenv"

    def ensure_root_dir(self) -> None:
        self._c.run(f"mkdir -p {self._maestro_root}")

    def ensure_pyenv_installed(self) -> None:
        result = self._c.run(f"ls {self._pyenv_root}", warn=True, hide="both")
        if result.ok:
            # Assume install succeeded.
            return

        try:
            # Need to install.
            install_script = pkg_resources.files(env_resources).joinpath(
                "install_pyenv.sh"
            )
            with pkg_resources.as_file(install_script) as path:
                self._c.put(path, f"{self._maestro_root}/install_pyenv.sh")
            # We want a custom install path to avoid interfering with the existing environment.
            self._c.run(
                f"bash {self._maestro_root}/install_pyenv.sh",
                env={"PYENV_ROOT": self._pyenv_root},
                hide="both",
            )
        except Exception:
            # If the installation failed, remove the directory so that we will
            # retry next time.
            self._c.run(f"rm -r {self._pyenv_root}")
            raise

    def install_python(self) -> None:
        self._c.run(
            f"{self._pyenv_root}/bin/pyenv install {MAESTRO_PYTHON_VERSION}",
            env={"PYENV_ROOT": self._pyenv_root},
        )
