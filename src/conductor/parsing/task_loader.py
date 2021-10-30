from conductor.task_types import raw_task_types
from conductor.errors import (
    ConductorError,
    DuplicateTaskName,
    MissingCondFile,
    ParsingUnknownNameError,
    TaskSyntaxError,
)
from conductor.task_types.stdlib import STDLIB_FILES


class TaskLoader:
    def __init__(self):
        self._tasks = None
        self._current_cond_file_path = None
        self._conductor_scope = self._compile_scope()

    def parse_cond_file(self, cond_file_path):
        """
        Parses all the tasks in a single COND file.
        """
        tasks = {}
        self._tasks = tasks
        self._current_cond_file_path = cond_file_path
        try:
            with open(cond_file_path, encoding="UTF-8") as file:
                code = file.read()
            # pylint: disable=exec-used
            exec(code, self._conductor_scope.copy())
            return tasks
        except ConductorError as ex:
            ex.add_file_context(file_path=cond_file_path)
            raise ex
        except SyntaxError as ex:
            syntax_err = TaskSyntaxError()
            syntax_err.add_file_context(
                file_path=cond_file_path,
                line_number=ex.lineno,
            )
            raise syntax_err from ex
        except NameError as ex:
            name_err = ParsingUnknownNameError(error_message=str(ex))
            name_err.add_file_context(file_path=cond_file_path)
            raise name_err from ex
        except FileNotFoundError as ex:
            missing_file_err = MissingCondFile()
            missing_file_err.add_file_context(file_path=cond_file_path)
            raise missing_file_err from ex
        finally:
            self._tasks = None
            self._current_cond_file_path = None

    def _compile_scope(self):
        scope = {}
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
