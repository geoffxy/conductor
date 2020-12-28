from conductor.errors import InvalidTaskIdentifier, TaskNotFound
from conductor.parsing.task_loader import TaskLoader
from conductor.task_identifier import TaskIdentifier
from conductor.user_code_utils import prevent_module_caching


class TaskIndex:
    def __init__(self, project_root):
        self._project_root = project_root
        self._task_loader = TaskLoader()
        # Keyed by the relative path to the COND file
        self._loaded_tasks = {}

    def get_task(self, identifier):
        """
        Returns the raw task associated with the specified identifier, if it
        has been loaded.
        """
        rel_path = identifier.path_to_cond_file()
        if (
            rel_path not in self._loaded_tasks
            or identifier.name not in self._loaded_tasks[rel_path]
        ):
            raise TaskNotFound(task_identifier=str(identifier))
        return self._loaded_tasks[rel_path][identifier.name]

    def load_transitive_closure(self, task_identifier):
        """
        Ensures all tasks in the transitive closure of the specified
        task_identifier are loaded.
        """
        identifiers_to_load = [task_identifier]
        visited_identifiers = set()

        with prevent_module_caching():
            while len(identifiers_to_load) > 0:
                identifier = identifiers_to_load.pop()
                if identifier in visited_identifiers:
                    continue

                visited_identifiers.add(identifier)
                rel_path = identifier.path_to_cond_file()
                if rel_path not in self._loaded_tasks:
                    self._loaded_tasks[rel_path] = self._task_loader.parse_cond_file(
                        identifier.path_to_cond_file(self._project_root),
                    )

                if identifier.name not in self._loaded_tasks[rel_path]:
                    raise TaskNotFound(task_identifier=str(identifier))

                raw_task = self._loaded_tasks[rel_path][identifier.name]
                try:
                    for dep in raw_task["deps"]:
                        identifiers_to_load.append(
                            TaskIdentifier.from_str(dep),
                        )
                except InvalidTaskIdentifier as ex:
                    ex.add_file_context(
                        identifier.path_to_cond_file(self._project_root),
                    )
                    raise
