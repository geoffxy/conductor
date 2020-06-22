from conductor.task_types import raw_task_types
from conductor.errors import DuplicateTask


class TaskLoader:
    def __init__(self):
        self._tasks = None
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
        try:
            with open(cond_file_path) as file:
                code = file.read()
            exec(code, self._task_constructors, self._task_constructors)
            return tasks
        finally:
            self._tasks = None

    def _wrap_task_function(self, task_constructor):
        def shim(**kwargs):
            raw_task = task_constructor(**kwargs)
            if raw_task["name"] in self._tasks:
                raise DuplicateTask(
                    "Task name '{}' was used more than once."
                    .format(raw_task["name"]),
                )
            self._tasks[raw_task["name"]] = raw_task
        return shim
