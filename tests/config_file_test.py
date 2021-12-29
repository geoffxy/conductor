import pathlib
import pytest

from conductor.config_file import ConfigFile
from conductor.errors import ConfigParseError, ConfigInvalidValue


def test_parse_error(tmp_path: pathlib.Path):
    test_file = tmp_path / "config.toml"
    with open(test_file, "w", encoding="UTF-8") as file:
        # Invalid TOML
        file.write("abcdefg!@#$%12345\n")

    with pytest.raises(ConfigParseError):
        ConfigFile.load_from_file(test_file)


def test_invalid_disable_git(tmp_path: pathlib.Path):
    test_file = tmp_path / "config.toml"
    with open(test_file, "w", encoding="UTF-8") as file:
        # Invalid `disable_git` value (should be a boolean)
        file.write("disable_git = 123\n")

    config = ConfigFile.load_from_file(test_file)
    with pytest.raises(ConfigInvalidValue):
        _ = config.disable_git


def test_valid_disable_git(tmp_path: pathlib.Path):
    test_file = tmp_path / "config.toml"
    with open(test_file, "w", encoding="UTF-8") as file:
        file.write("disable_git = true\n")

    config = ConfigFile.load_from_file(test_file)
    assert config.disable_git == True
