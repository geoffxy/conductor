import re
from conductor.errors import InvalidTaskIdentifier

_IDENTIFIER_GROUP = "[a-zA-Z0-9_-]+"
_NAME_REGEX = re.compile("^{}$".format(_IDENTIFIER_GROUP))
_TARGET_IDENTIFIER_REGEX = re.compile(
    "^(//)?(?P<path>({}/)*({})?):(?P<name>{})$"
        .format(_IDENTIFIER_GROUP, _IDENTIFIER_GROUP, _IDENTIFIER_GROUP),
)


class TaskIdentifier:
    def __init__(self, path, name):
        self._path = path
        self._name = name

    def __repr__(self):
        return "".join(
            ["//", "/".join(self._path), ":", self._name],
        )

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @classmethod
    def from_str(cls, candidate, require_prefix=True):
        match = _TARGET_IDENTIFIER_REGEX.match(candidate)
        if match is None:
            raise InvalidTaskIdentifier(candidate)
        if require_prefix and not candidate.startswith("//"):
            raise InvalidTaskIdentifier(candidate)

        path = match.group("path")
        if path is None:
            path = []
        else:
            path = list(filter(lambda s: len(s) > 0, path.split("/")))

        return cls(path=path, name=match.group("name"))

    @staticmethod
    def is_name_valid(candidate):
        return _NAME_REGEX.match(candidate) is not None
