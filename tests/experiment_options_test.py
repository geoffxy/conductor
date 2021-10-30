import pytest

import json
import pathlib
from typing import Dict

from conductor.errors import (
    ExperimentOptionsNonPrimitiveValue,
    ExperimentOptionsNonStringKey,
)
from conductor.task_identifier import TaskIdentifier
from conductor.utils.experiment_options import ExperimentOptions, OptionValue


def assert_serialized_cmdline(cmd_options: str, raw_options: Dict[str, OptionValue]):
    pieces = cmd_options.split(" ")
    assert len(pieces) == len(raw_options)
    for option in pieces:
        key, value = option.split("=")
        key_without_leading = key[2:]
        assert key_without_leading in raw_options
        if isinstance(raw_options[key_without_leading], bool):
            assert value == ("true" if raw_options[key_without_leading] else "false")
        else:
            assert value == str(raw_options[key_without_leading])


def assert_serialized_json(
    json_path: pathlib.Path, raw_options: Dict[str, OptionValue]
):
    assert json_path.is_file()

    with open(json_path, "r", encoding="UTF-8") as file:
        loaded = json.load(file)
    assert loaded == raw_options


def test_valid(tmp_path: pathlib.Path):
    simple: Dict[str, OptionValue] = {
        "hello": 1,
        "world": "hello",
        "key": True,
        "key2": 3.14159,
    }
    identifier = TaskIdentifier.from_str("//test:ident")
    simple_options = ExperimentOptions.from_raw(identifier, simple)
    assert not simple_options.empty()

    # Test command line serialization
    cmd_options = simple_options.serialize_cmdline()
    assert len(cmd_options) > 0
    assert_serialized_cmdline(cmd_options, simple)

    # Test JSON serialization
    json_file = tmp_path / "options.json"
    simple_options.serialize_json(json_file)
    assert_serialized_json(json_file, simple)


def test_single_option(tmp_path: pathlib.Path):
    single: Dict[str, OptionValue] = {
        "key": "value",
    }
    identifier = TaskIdentifier.from_str("//test:ident")
    options = ExperimentOptions.from_raw(identifier, single)
    assert not options.empty()

    # Test command line serialization
    cmd_options = options.serialize_cmdline()
    assert len(cmd_options) > 0
    assert_serialized_cmdline(cmd_options, single)

    # Test JSON serialization
    json_file = tmp_path / "options.json"
    options.serialize_json(json_file)
    assert_serialized_json(json_file, single)


def test_empty():
    empty: Dict[str, OptionValue] = {}
    identifier = TaskIdentifier.from_str("//test:ident")
    options = ExperimentOptions.from_raw(identifier, empty)
    assert options.empty()
    assert options.serialize_cmdline() == ""


def test_non_string_key():
    numeric_key = {
        "hello": "world",
        3: "asd",
    }
    tuple_key = {
        (1, 2): "test",
        "foo": "bar",
    }
    identifier = TaskIdentifier.from_str("//test:ident")
    with pytest.raises(ExperimentOptionsNonStringKey):
        ExperimentOptions.from_raw(identifier, numeric_key)
    with pytest.raises(ExperimentOptionsNonStringKey):
        ExperimentOptions.from_raw(identifier, tuple_key)


def test_non_primitive_value():
    nested_value = {
        "hello": "world",
        "nested": {
            "value": 1,
        },
    }
    tuple_value = {
        "value": (1, 2, 3),
        "key": "value",
    }

    identifier = TaskIdentifier.from_str("//test:ident")
    with pytest.raises(ExperimentOptionsNonPrimitiveValue):
        ExperimentOptions.from_raw(identifier, nested_value)
    with pytest.raises(ExperimentOptionsNonPrimitiveValue):
        ExperimentOptions.from_raw(identifier, tuple_value)
