import pathlib
from typing import Dict, Set

from conductor.errors import (
    ConductorError,
    CyclicDependency,
    DuplicateDependency,
    TaskNotFound,
)
from conductor.parsing.task_loader import TaskLoader
from conductor.task_identifier import TaskIdentifier
from conductor.utils.user_code import prevent_module_caching
from conductor.task_types.base import TaskType


class TaskIndex:
    def __init__(self, project_root: pathlib.Path):
        self._project_root = project_root
        self._task_loader = TaskLoader(project_root)
        # Keyed by the relative path to the COND file
        self._loaded_raw_tasks: Dict[pathlib.Path, Dict[str, Dict]] = {}
        # Keyed by task identifier
        self._loaded_tasks: Dict[TaskIdentifier, TaskType] = {}

    def get_task(self, identifier: TaskIdentifier) -> TaskType:
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
            rel_path not in self._loaded_raw_tasks
            or identifier.name not in self._loaded_raw_tasks[rel_path]
        ):
            raise TaskNotFound(task_identifier=str(identifier))

        self._loaded_tasks[identifier] = self._materialize_raw_task(
            identifier, self._loaded_raw_tasks[rel_path][identifier.name]
        )
        return self._loaded_tasks[identifier]

    def load_transitive_closure(self, task_identifier: TaskIdentifier):
        """
        Ensures all tasks in the transitive closure of the specified
        `task_identifier` are loaded.

        This method will raise the appropriate errors if there are problems
        loading the needed tasks. This method will also check to ensure there
        are no cycles in the dependency graph.
        """
        identifiers_to_load = [(task_identifier, 0)]
        visited_identifiers = set()
        curr_path: Set[TaskIdentifier] = set()

        with prevent_module_caching():
            while len(identifiers_to_load) > 0:
                identifier, visit_count = identifiers_to_load.pop()

                if visit_count > 0:
                    # We've finished processing this task's children
                    curr_path.remove(identifier)
                    visited_identifiers.add(identifier)
                    continue

                if identifier in curr_path:
                    # The user's dependency graph contains a cycle
                    raise CyclicDependency(
                        task_identifier=task_identifier
                    ).add_file_context(
                        task_identifier.path_to_cond_file(self._project_root)
                    )

                try:
                    self.load_single_task(identifier)
                except TaskNotFound as e:
                    raise e.add_extra_context(
                        "This error occurred when resolving the transitive dependencies of task '{}'.".format(
                            str(task_identifier)
                        )
                    )

                identifiers_to_load.append((identifier, 1))
                curr_path.add(identifier)

                for dep in self._loaded_tasks[identifier].deps:
                    if dep in visited_identifiers:
                        continue
                    identifiers_to_load.append((dep, 0))

    def load_single_task(self, identifier: TaskIdentifier):
        """
        Loads only the task specified by `identifier`.
        """
        rel_path = identifier.path_to_cond_file()
        if rel_path not in self._loaded_raw_tasks:
            self._loaded_raw_tasks[rel_path] = self._task_loader.parse_cond_file(
                identifier.path_to_cond_file(self._project_root),
            )

        if identifier.name not in self._loaded_raw_tasks[rel_path]:
            raise TaskNotFound(task_identifier=str(identifier)).add_file_context(
                identifier.path_to_cond_file(self._project_root)
            )

        raw_task = self._loaded_raw_tasks[rel_path][identifier.name]
        self._loaded_tasks[identifier] = self._materialize_raw_task(
            identifier, raw_task
        )

    def _materialize_raw_task(
        self, identifier: TaskIdentifier, raw_task: Dict
    ) -> TaskType:
        try:
            raw_task = raw_task.copy()
            task_deps = []
            task_deps_set = set()
            if "deps" in raw_task:
                for dep in raw_task["deps"]:
                    # When defining task dependencies, we allow users to use "relative"
                    # task identifiers to refer to tasks defined in the same COND file.
                    if TaskIdentifier.is_relative_candidate(dep):
                        dep_identifier = TaskIdentifier.from_relative_str(
                            dep, identifier.path
                        )
                    else:
                        dep_identifier = TaskIdentifier.from_str(dep)
                    if dep_identifier in task_deps_set:
                        raise DuplicateDependency(
                            task_identifier=identifier, dep_identifier=dep_identifier
                        )
                    task_deps.append(dep_identifier)
                    task_deps_set.add(dep_identifier)
                del raw_task["deps"]

            return TaskType.from_raw_task(identifier, raw_task, task_deps)

        except ConductorError as ex:
            ex.add_file_context(
                identifier.path_to_cond_file(self._project_root),
            )
            raise
