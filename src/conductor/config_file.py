import tomli
import pathlib

from typing import Any, Dict
from conductor.errors import ConfigParseError, ConfigInvalidValue


class ConfigFile:
    def __init__(self, raw_config: Dict[str, Any]):
        self._raw_config = raw_config

    @classmethod
    def load_from_file(cls, filepath: pathlib.Path) -> "ConfigFile":
        try:
            with open(filepath, "rb") as file:
                return cls(raw_config=tomli.load(file))
        except tomli.TOMLDecodeError as ex:
            raise ConfigParseError().add_extra_context(str(ex))

    @property
    def disable_git(self) -> bool:
        # Disables Conductor's git integration.
        # Default: False
        if _DISABLE_GIT_KEY not in self._raw_config:
            return False
        value = self._raw_config[_DISABLE_GIT_KEY]
        if type(value) is not bool:
            raise ConfigInvalidValue(config_key=_DISABLE_GIT_KEY).add_extra_context(
                "The value must be a boolean."
            )
        return value


# Config keys (global)
_DISABLE_GIT_KEY = "disable_git"
