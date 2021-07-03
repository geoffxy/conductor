import pathlib
import re

from conductor.config import COND_FILE_NAME
from conductor.errors import InvalidTaskIdentifier

IDENTIFIER_GROUP = "[a-zA-Z0-9_-]+"
_NAME_REGEX = re.compile("^{}$".format(IDENTIFIER_GROUP))
_TASK_IDENTIFIER_REGEX = re.compile(
    "^(//)?(?P<path>({ident}/)*({ident})?):(?P<name>{ident})$".format(
        ident=IDENTIFIER_GROUP,
    ),
)
_RELATIVE_TASK_IDENTIFIER_REGEX = re.compile(
    "^:(?P<name>{ident})$".format(ident=IDENTIFIER_GROUP)
)


class TaskIdentifier:
    def __init__(self, path: pathlib.Path, name: str):
        self._path = path
        self._name = name

    def __repr__(self) -> str:
        return "".join(
            ["//", "/".join(self._path.parts), ":", self._name],
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskIdentifier):
            raise NotImplementedError

        return self.path == other.path and self.name == other.name

    def __hash__(self):
        return hash(self.__repr__())

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def name(self) -> str:
        return self._name

    def path_to_cond_file(self, project_root=None) -> pathlib.Path:
        """
        Returns a path to the COND file where this task should be declared.

        If a project root is specified, this method will return an absolute
        path to the COND file. Otherwise this method returns a path relative to
        the project root.
        """
        if project_root is not None:
            return pathlib.Path(project_root, self._path, COND_FILE_NAME)
        else:
            return pathlib.Path(self._path, COND_FILE_NAME)

    def relative_with_name(self, name: str) -> "TaskIdentifier":
        return TaskIdentifier(self._path, name)

    @classmethod
    def from_str(cls, candidate: str, require_prefix: bool = True) -> "TaskIdentifier":
        match = _TASK_IDENTIFIER_REGEX.match(candidate)
        if match is None:
            raise InvalidTaskIdentifier(task_identifier=candidate)
        if require_prefix and not candidate.startswith("//"):
            raise InvalidTaskIdentifier(task_identifier=candidate)

        path_str = match.group("path")
        if path_str is None:
            path = pathlib.Path()
        else:
            path = pathlib.Path(*filter(lambda s: len(s) > 0, path_str.split("/")))

        return cls(path=path, name=match.group("name"))

    @classmethod
    def from_relative_str(
        cls, candidate: str, rel_cond_file_dir: pathlib.Path
    ) -> "TaskIdentifier":
        """
        Constructs a task identifier using a candidate relative task
        identifier (e.g., ":task_name"). Relative task identifiers are
        permitted in the `deps` field of a task to refer to tasks defined in
        the same COND file.

        The caller must provide a path to the directory containing the COND
        file where the task is defined.
        """
        match = _RELATIVE_TASK_IDENTIFIER_REGEX.match(candidate)
        if match is None:
            raise InvalidTaskIdentifier(task_identifier=candidate)
        return cls(path=rel_cond_file_dir, name=match.group("name"))

    @staticmethod
    def is_name_valid(candidate: str) -> bool:
        return _NAME_REGEX.match(candidate) is not None

    @staticmethod
    def is_relative_candidate(candidate: str) -> bool:
        """
        Returns true if `candidate` might be a valid relative task
        identifier. If the method returns true, `candidate` should be passed
        to `TaskIdentifier.from_relative_string()`. If the method returns
        false, you should use `TaskIdentifier.from_str()` instead.
        """
        return candidate.startswith(":")
