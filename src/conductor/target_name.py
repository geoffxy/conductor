import re
from conductor.errors import InvalidTargetName

_IDENTIFIER_GROUP = "[a-zA-Z0-9_-]+"
_IDENTIFIER_REGEX = re.compile("^{}$".format(_IDENTIFIER_GROUP))
_TARGET_NAME_REGEX = re.compile(
    "^(//)?(?P<path>({}/)*({})?):(?P<identifier>{})$"
        .format(_IDENTIFIER_GROUP, _IDENTIFIER_GROUP, _IDENTIFIER_GROUP),
)


class TargetName:
    def __init__(self, path, identifier):
        self._path = path
        self._identifier = identifier

    def __repr__(self):
        return "".join(
            ["//", "/".join(self._path), ":", self._identifier],
        )

    @classmethod
    def from_str(cls, candidate, require_prefix=True):
        match = _TARGET_NAME_REGEX.match(candidate)
        if match is None:
            raise InvalidTargetName(candidate)
        if require_prefix and not candidate.startswith("//"):
            raise InvalidTargetName(candidate)

        path = match.group("path")
        if path is None:
            path = []
        else:
            path = list(filter(lambda s: len(s) > 0, path.split("/")))

        return cls(path=path, identifier=match.group("identifier"))

    @staticmethod
    def is_identifier_valid(candidate):
        return _IDENTIFIER_REGEX.match(candidate) is not None
