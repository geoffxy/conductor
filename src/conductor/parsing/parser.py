import contextlib
import os
import sys

from conductor.task_types import raw_task_types


class Parser:
    def __init__(self, project_root):
        self._project_root = project_root
        self._tasks = None
        self._rule_constructors = {}
        for raw_task_type in raw_task_types.values():
            self._rule_constructors[raw_task_type.name] = (
                self._wrap_task_function(raw_task_type.load_from_cond_file)
            )

    def parse_cond_file(self, task_identifier):
        """
        Parses all the tasks in a single COND file.
        """
        cond_file_path = os.path.join(
            self._project_root,
            *task_identifier.path,
            "COND",
        )
        tasks = []
        self._tasks = tasks
        try:
            with open(cond_file_path) as file:
                code = file.read()
            with prevent_module_caching():
                exec(code, self._rule_constructors, self._rule_constructors)
            return tasks
        finally:
            self._tasks = None

    def _wrap_task_function(self, task_constructor):
        def shim(**kwargs):
            self._tasks.append(task_constructor(**kwargs))
        return shim


@contextlib.contextmanager
def prevent_module_caching():
    """
    A context manager that prevents any imported modules from being cached
    after exiting.
    """
    original_modules = sys.modules.copy()
    try:
        yield
    finally:
        newly_added = {
            module_name for module_name in sys.modules.keys()
            if module_name not in original_modules
        }
        for module_name in newly_added:
            del sys.modules[module_name]
