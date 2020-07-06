from conductor.task_types import raw_task_types
from conductor.errors import (
    ConductorError,
    DuplicateTaskName,
    ParsingUnknownNameError,
    TaskSyntaxError,
)


class TaskLoader:
    def __init__(self):
        self._tasks = None
        self._current_cond_file_path = None
        self._task_constructors = {}
        for raw_task_type in raw_task_types.values():
            self._task_constructors[raw_task_type.name] = (
                self._wrap_task_function(raw_task_type.load_from_cond_file)
            )

    def parse_cond_file(self, cond_file_path):
        """
        Parses all the tasks in a single COND file.
        """
        tasks = {}
        self._tasks = tasks
        self._current_cond_file_path = cond_file_path
        try:
            with open(cond_file_path) as file:
                code = file.read()
            exec(code, self._task_constructors, self._task_constructors)
            return tasks
        except ConductorError as error:
            error.add_file_context(file_path=cond_file_path)
            raise error
        except SyntaxError as ex:
            error = TaskSyntaxError()
            error.add_file_context(
                file_path=cond_file_path,
                line_number=ex.lineno,
            )
            raise error
        except NameError as ex:
            error = ParsingUnknownNameError(error_message=str(ex))
            error.add_file_context(file_path=cond_file_path)
            raise error
        finally:
            self._tasks = None
            self._current_cond_file_path = None

    def _wrap_task_function(self, task_constructor):
        def shim(**kwargs):
            raw_task = task_constructor(**kwargs)
            raw_task["cond_file_path"] = self._current_cond_file_path
            if raw_task["name"] in self._tasks:
                raise DuplicateTaskName(task_name=raw_task["name"])
            self._tasks[raw_task["name"]] = raw_task
        return shim
