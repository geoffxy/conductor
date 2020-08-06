import os
import re

from conductor.config import COND_FILE_NAME
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

    def __eq__(self, other):
        return (
            len(self.path) == len(other.path) and
            all(map(
                lambda segments: segments[0] == segments[1],
                zip(self.path, other.path),
            )) and
            self.name == other.name
        )

    def __hash__(self):
        return hash(self.__repr__())

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    def path_to_cond_file(self, project_root=None):
        """
        Returns a path to the COND file where this task should be declared.

        If a project root is specified, this method will return an absolute
        path to the COND file. Otherwise this method returns a path relative to
        the project root.
        """
        if project_root is not None:
            return os.path.join(project_root, *self._path, COND_FILE_NAME)
        else:
            return os.path.join(*self._path, COND_FILE_NAME)

    def relative_with_name(self, name):
        return TaskIdentifier(self._path, name)

    @classmethod
    def from_str(cls, candidate, require_prefix=True):
        match = _TARGET_IDENTIFIER_REGEX.match(candidate)
        if match is None:
            raise InvalidTaskIdentifier(task_identifier=candidate)
        if require_prefix and not candidate.startswith("//"):
            raise InvalidTaskIdentifier(task_identifier=candidate)

        path = match.group("path")
        if path is None:
            path = []
        else:
            path = list(filter(lambda s: len(s) > 0, path.split("/")))

        return cls(path=path, name=match.group("name"))

    @staticmethod
    def is_name_valid(candidate):
        return _NAME_REGEX.match(candidate) is not None
