import pytest

import pathlib
import itertools

from conductor.errors import InvalidTaskIdentifier
from conductor.task_identifier import TaskIdentifier


def test_fully_qualified():
    valid = [
        "//abc:abc",
        "//:abc",
        "//foo/bar/def:abc",
        "//test/one-folder:abc_123",
        "//123:123",
        "//:1",
    ]
    for candidate in valid:
        ident = TaskIdentifier.from_str(candidate, require_prefix=True)
        assert ident is not None
        assert candidate == str(ident)

    # We allow trailing slashes (/) before the task name, but remove them in
    # the task identifier's canonical representation
    trailing = "//abc/abc/:abc"
    ident = TaskIdentifier.from_str(trailing, require_prefix=True)
    assert ident is not None
    assert str(ident) == "//abc/abc:abc"


def test_invalid_fully_qualified():
    invalid = [
        "//abc",
        ":foo",
        "bar",
        "abc/abc/abc:abc",
        "//abc/def/abc/abc",
        "//abc:abc:abc",
        "a:a:a",
        "asd123def123-1231",
        "//*&@#:###",
    ]
    for candidate in invalid:
        with pytest.raises(InvalidTaskIdentifier):
            _ = TaskIdentifier.from_str(candidate, require_prefix=True)


def test_unprefixed_fully_qualified():
    valid = [
        ":abc",
        ":_123",
        "abc/abc:abc",
        "abc/123/123:234",
        "dir-123/test:test",
    ]
    for candidate in valid:
        ident = TaskIdentifier.from_str(candidate, require_prefix=False)
        assert ident is not None
        assert "//" + candidate == str(ident)

    trailing = "abc/abc/:abc"
    ident = TaskIdentifier.from_str(trailing, require_prefix=False)
    assert ident is not None
    assert str(ident) == "//abc/abc:abc"


def test_relative():
    valid = [
        ":abc",
        ":123",
        ":abc-123_321",
        ":very_long_name",
        ":000abc",
    ]
    paths = [pathlib.Path(), pathlib.Path("foo"), pathlib.Path("foo", "bar")]
    for path, candidate in itertools.product(paths, valid):
        ident = TaskIdentifier.from_relative_str(candidate, path)
        assert ident is not None
        assert ident.path == path
        assert ident.name == candidate[1:]


def test_invalid_relative():
    invalid = [
        "//abc:abc",
        "//def",
        "abc/abc:abc",
        "abc:abc",
        ":abc/def",
        "//abc/:123",
        ":abc:abc",
    ]
    paths = [pathlib.Path(), pathlib.Path("foo"), pathlib.Path("foo", "bar")]
    for path, candidate in itertools.product(paths, invalid):
        with pytest.raises(InvalidTaskIdentifier):
            _ = TaskIdentifier.from_relative_str(candidate, path)
