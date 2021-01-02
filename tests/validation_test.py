import pytest

from conductor.errors import (
    InvalidTaskParameterType,
    MissingTaskParameter,
    UnrecognizedTaskParameters,
)
from conductor.parsing.validation import generate_type_validator

# pylint: disable=redefined-outer-name


@pytest.fixture
def simple_schema_validator():
    schema = {"string": str, "numeric": int, "boolean": bool}
    return generate_type_validator("Task", schema)


@pytest.fixture
def schema_with_lists_validator():
    schema = {"prop": str, "strlist": [str], "intlist": [int]}
    return generate_type_validator("Task", schema)


def test_simple(simple_schema_validator):
    simple_schema_validator({"string": "foo", "numeric": 20, "boolean": True})


def test_incorrect_types(simple_schema_validator):
    with pytest.raises(InvalidTaskParameterType):
        simple_schema_validator({"string": "foo", "numeric": "20", "boolean": True})

    with pytest.raises(InvalidTaskParameterType):
        simple_schema_validator({"string": "foo", "numeric": [20], "boolean": True})


def test_missing_properties(simple_schema_validator):
    with pytest.raises(MissingTaskParameter):
        simple_schema_validator({"string": "foo", "boolean": True})

    with pytest.raises(MissingTaskParameter):
        simple_schema_validator({"numeric": 20, "boolean": True})

    with pytest.raises(MissingTaskParameter):
        simple_schema_validator({"string": "foo"})


def test_extraneous_properties(simple_schema_validator):
    valid = {"string": "foo", "numeric": 20, "boolean": True}
    with pytest.raises(UnrecognizedTaskParameters):
        simple_schema_validator({**valid, "unknown": 1})

    with pytest.raises(UnrecognizedTaskParameters):
        simple_schema_validator({**valid, "extra": 1, "extra2": "123"})


def test_list_simple(schema_with_lists_validator):
    schema_with_lists_validator(
        {"prop": "hello", "strlist": ["abc"], "intlist": [1, 2, 3]}
    )


def test_list_mixed_types(schema_with_lists_validator):
    with pytest.raises(InvalidTaskParameterType):
        schema_with_lists_validator(
            {"prop": "hello", "strlist": ["abc", "def"], "intlist": [1, 2, "3"]}
        )
    with pytest.raises(InvalidTaskParameterType):
        schema_with_lists_validator(
            {"prop": "hello", "strlist": ["abc", "def", True], "intlist": [1, 2, 3]}
        )


def test_list_wrong_type(schema_with_lists_validator):
    with pytest.raises(InvalidTaskParameterType):
        schema_with_lists_validator(
            {"prop": "hello", "strlist": [123, False, True], "intlist": [1, 2, 3]}
        )
