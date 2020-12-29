from conductor.errors import InvalidTaskIdentifier, TaskNotFound
from conductor.parsing.task_loader import TaskLoader
from conductor.task_identifier import TaskIdentifier
from conductor.user_code_utils import prevent_module_caching
from conductor.task_types.base import TaskType


class TaskIndex:
    def __init__(self, project_root):
        self._project_root = project_root
        self._task_loader = TaskLoader()
        # Keyed by the relative path to the COND file
        self._loaded_raw_tasks = {}
        # Keyed by task identifier
        self._loaded_tasks = {}

    def get_task(self, identifier):
        """
        Returns the task associated with the specified identifier, if it
        has been loaded.
        """
        if identifier in self._loaded_tasks:
            return self._loaded_tasks[identifier]

        # Check if we have the raw task loaded - if so, materialize it and then
        # return it
        rel_path = identifier.path_to_cond_file()
        if (
            rel_path not in self._loaded_tasks
            or identifier.name not in self._loaded_tasks[rel_path]
        ):
            raise TaskNotFound(task_identifier=str(identifier))

        self._loaded_tasks[identifier] = self._materialize_raw_task(
            identifier, self._loaded_raw_tasks[rel_path][identifier.name]
        )
        return self._loaded_tasks[identifier]

    def load_transitive_closure(self, task_identifier):
        """
        Ensures all tasks in the transitive closure of the specified
        `task_identifier` are loaded.
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
                if rel_path not in self._loaded_raw_tasks:
                    self._loaded_raw_tasks[
                        rel_path
                    ] = self._task_loader.parse_cond_file(
                        identifier.path_to_cond_file(self._project_root),
                    )

                if identifier.name not in self._loaded_raw_tasks[rel_path]:
                    raise TaskNotFound(
                        task_identifier=str(identifier)
                    ).add_file_context(
                        task_identifier.path_to_cond_file(self._project_root)
                    ).add_extra_context(
                        "This error occurred when resolving the transitive dependencies of task '{}'.".format(
                            str(task_identifier)
                        )
                    )

                raw_task = self._loaded_raw_tasks[rel_path][identifier.name]
                self._loaded_tasks[identifier] = self._materialize_raw_task(
                    identifier, raw_task
                )

                for dep in self._loaded_tasks[identifier].deps:
                    identifiers_to_load.append(dep)

    def _materialize_raw_task(self, identifier, raw_task):
        try:
            raw_task = raw_task.copy()
            task_deps = []
            if "deps" in raw_task:
                for dep in raw_task["deps"]:
                    task_deps.append(TaskIdentifier.from_str(dep))
                del raw_task["deps"]
            return TaskType.from_raw_task(identifier, raw_task, task_deps)

        except InvalidTaskIdentifier as ex:
            ex.add_file_context(
                identifier.path_to_cond_file(self._project_root),
            )
            raise
