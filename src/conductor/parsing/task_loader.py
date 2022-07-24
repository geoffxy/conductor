import pathlib
from typing import Any, Dict, Optional
from conductor.config import COND_INCLUDE_EXTENSION
from conductor.task_types import raw_task_types
from conductor.errors import (
    ConductorError,
    DuplicateTaskName,
    MissingCondFile,
    ParsingUnknownNameError,
    TaskSyntaxError,
    TaskParseError,
    IncludeFileInvalidExtension,
    IncludeFileNotFound,
    IncludeFileNotInProject,
)
from conductor.task_types.stdlib import STDLIB_FILES


class TaskLoader:
    def __init__(self, project_root: pathlib.Path):
        self._project_root = project_root
        self._tasks: Optional[Dict[str, Dict]] = None
        self._current_cond_file_path: Optional[pathlib.Path] = None
        self._conductor_scope = self._compile_scope()
        self._curr_exec_scope = None

        # We cache the results from evaluating `include()`s so that if a file is
        # included across multiple `COND` files, we do not repeatedly evaluate
        # the file. The code being included is expected to be deterministic.
        #
        # Key is the absolute path to the file (e.g. /home/user/path/to/file.cond).
        # Value is the resulting scope object.
        self._include_cache: Dict[str, Any] = {}

    def parse_cond_file(self, cond_file_path: pathlib.Path):
        """
        Parses all the tasks in a single COND file.
        """
        tasks: Dict[str, Dict] = {}
        self._tasks = tasks
        self._current_cond_file_path = cond_file_path
        try:
            with open(cond_file_path, encoding="UTF-8") as file:
                code = file.read()
            self._curr_exec_scope = self._conductor_scope.copy()
            # pylint: disable=exec-used
            exec(code, self._curr_exec_scope)
            return tasks
        except ConductorError as ex:
            ex.add_file_context_if_missing(
                file_path=self._to_project_path(cond_file_path)
            )
            raise ex
        except SyntaxError as ex:
            syntax_err = TaskSyntaxError()
            syntax_err.add_file_context(
                file_path=self._to_project_path(cond_file_path),
                line_number=ex.lineno,
            )
            raise syntax_err from ex
        except NameError as ex:
            name_err = ParsingUnknownNameError(error_message=str(ex))
            name_err.add_file_context(file_path=self._to_project_path(cond_file_path))
            raise name_err from ex
        except FileNotFoundError as ex:
            missing_file_err = MissingCondFile()
            missing_file_err.add_file_context(
                file_path=self._to_project_path(cond_file_path)
            )
            raise missing_file_err from ex
        except Exception as ex:
            run_err = TaskParseError(error_details=str(ex))
            run_err.add_file_context(file_path=self._to_project_path(cond_file_path))
            raise run_err from ex
        finally:
            self._tasks = None
            self._current_cond_file_path = None
            self._curr_exec_scope = None

    def _compile_scope(self):
        scope = {
            # Used to handle included files.
            "include": self._run_include,
        }
        # Create the task constructors for Conductor's foundational task types.
        for raw_task_type in raw_task_types.values():
            scope[raw_task_type.name] = self._wrap_task_function(
                raw_task_type.load_from_cond_file
            )
        # We need to explicitly `compile()` the Conductor standard library
        # files here to ensure that any uses of Conductor's foundational task
        # types bind to the task constructors defined above.
        for lib_file_path in STDLIB_FILES:
            with open(lib_file_path, "r", encoding="UTF-8") as lib_file:
                code = compile(lib_file.read(), str(lib_file_path), "exec")
            # pylint: disable=exec-used
            exec(code, scope)
        return scope

    def _wrap_task_function(self, task_constructor):
        def shim(**kwargs):
            raw_task = task_constructor(**kwargs)
            raw_task["cond_file_path"] = self._current_cond_file_path
            if raw_task["name"] in self._tasks:
                raise DuplicateTaskName(task_name=raw_task["name"])
            self._tasks[raw_task["name"]] = raw_task

        return shim

    def _run_include(self, candidate_path: str):
        assert self._current_cond_file_path is not None
        assert self._curr_exec_scope is not None

        # 1. Validate `candidate_path`.
        if not candidate_path.endswith(COND_INCLUDE_EXTENSION):
            raise IncludeFileInvalidExtension(included_file=candidate_path)

        # 2. Parse `candidate_path`.
        if candidate_path.startswith("//"):
            include_path = self._project_root.joinpath(candidate_path[2:])
        else:
            include_path = self._current_cond_file_path.parent.joinpath(candidate_path)
        try:
            include_path = include_path.resolve(strict=True)
        except FileNotFoundError as ex:
            raise IncludeFileNotFound(included_file=candidate_path) from ex

        # 3. Make sure `include_path` is inside our project.
        # If `include_path` is not relative to `self._project_root` then the
        # method will raise a `ValueError`. For compatibility with Python 3.8,
        # we do not use `is_relative_to()` (it is a Python 3.9+ method).
        try:
            include_path.relative_to(self._project_root)
        except ValueError as ex:
            raise IncludeFileNotInProject(included_file=candidate_path) from ex

        # 4. Check if the file is in our cache. If so, just use the cached results.
        if str(include_path) in self._include_cache:
            self._curr_exec_scope.update(self._include_cache[str(include_path)])
            return

        # 5. Run the included file. We purposely use a separate scope so that
        # the Conductor task symbols (e.g., run_experiment()) are not available
        # in the included file.
        with open(include_path, encoding="UTF-8") as file:
            include_code = file.read()
        scope: Dict[str, Any] = {}
        try:
            # pylint: disable=exec-used
            exec(include_code, {}, scope)
        except SyntaxError as ex:
            syntax_err = TaskSyntaxError()
            syntax_err.add_file_context(
                file_path=self._to_project_path(include_path),
                line_number=ex.lineno,
            ).add_extra_context(
                "This error occurred while parsing a file included by {}.".format(
                    self._to_project_path(self._current_cond_file_path)
                )
            )
            raise syntax_err from ex
        except Exception as ex:
            run_err = TaskParseError(error_details=str(ex))
            run_err.add_file_context(
                file_path=self._to_project_path(include_path)
            ).add_extra_context(
                "This error occurred while parsing a file included by {}.".format(
                    self._to_project_path(self._current_cond_file_path)
                )
            )
            raise run_err from ex

        # 6. Update the current scope with the new symbols.
        self._curr_exec_scope.update(scope)

        # 7. Update the cache.
        self._curr_exec_scope[str(include_path)] = scope

    def _to_project_path(self, path: pathlib.Path) -> str:
        """Converts the given path to a path that is relative to the project root."""
        rel_path = path.relative_to(self._project_root)
        return "//{}".format(rel_path)
