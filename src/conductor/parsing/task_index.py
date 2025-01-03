import pathlib
from typing import Dict, Set, List, Tuple, Optional

from conductor.config import COND_FILE_NAME
from conductor.errors import (
    ConductorError,
    CyclicDependency,
    DuplicateDependency,
    TaskNotFound,
    EnvNotFound,
    EnvNotEnv,
    DuplicateEnvName,
)
from conductor.parsing.task_loader import TaskLoader
from conductor.task_identifier import TaskIdentifier
from conductor.task_types.base import TaskType
from conductor.utils.user_code import prevent_module_caching
from conductor.utils.git import Git
from conductor.task_types.environment import Environment
from conductor.task_types.run import RunCommand, RunExperiment


class TaskIndex:
    def __init__(self, project_root: pathlib.Path):
        self._project_root = project_root
        self._task_loader = TaskLoader(project_root)
        # Keyed by the relative path to the COND file
        self._loaded_raw_tasks: Dict[pathlib.Path, Dict[str, Dict]] = {}
        # Keyed by task identifier
        self._loaded_tasks: Dict[TaskIdentifier, TaskType] = {}
        # Used to manage task loading caching. If we have called
        # `load_all_known_tasks()` before, we avoid running it again.
        self._all_loaded = False
        self._loaded_envs: Dict[str, Environment] = {}

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

    def get_all_loaded_tasks(self) -> Dict[TaskIdentifier, TaskType]:
        """
        Returns all loaded tasks.
        """
        return self._loaded_tasks

    def load_transitive_closure(self, task_identifier: TaskIdentifier):
        """
        Ensures all tasks in the transitive closure of the specified
        `task_identifier` are loaded.

        This method will raise the appropriate errors if there are problems
        loading the needed tasks. This method will also check to ensure there
        are no cycles in the dependency graph.
        """
        identifiers_to_load = [(task_identifier, False, 0)]
        visited_identifiers = set()
        curr_path: Set[TaskIdentifier] = set()

        with prevent_module_caching():
            while len(identifiers_to_load) > 0:
                identifier, expect_env, visit_count = identifiers_to_load.pop()

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
                    extra_context = (
                        "This error occurred when resolving the transitive dependencies "
                        f"of task '{str(task_identifier)}'."
                    )
                    if not expect_env:
                        raise e.add_extra_context(extra_context)
                    else:
                        raise EnvNotFound(
                            env_name=str(identifier.name)
                        ).add_extra_context(extra_context)

                identifiers_to_load.append((identifier, expect_env, 1))
                curr_path.add(identifier)

                loaded_task = self._loaded_tasks[identifier]
                if expect_env and not isinstance(loaded_task, Environment):
                    raise EnvNotEnv(task_identifier=str(identifier)).add_extra_context(
                        "This error occurred when resolving the transitive dependencies "
                        f"of task '{str(task_identifier)}'."
                    )

                for dep in loaded_task.deps:
                    if dep in visited_identifiers:
                        continue
                    identifiers_to_load.append((dep, False, 0))

                # Special case: `run_experiment()` and `run_command()` can run
                # in a remote environment. Environments are defined as a special
                # "task type", so we need to load them here too.
                if isinstance(loaded_task, RunExperiment) or isinstance(
                    loaded_task, RunCommand
                ):
                    if (
                        loaded_task.env is not None
                        and loaded_task.env not in visited_identifiers
                    ):
                        identifiers_to_load.append((loaded_task.env, True, 0))

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
        materialized_task = self._materialize_raw_task(identifier, raw_task)

        if isinstance(materialized_task, Environment):
            if identifier.name in self._loaded_envs:
                raise DuplicateEnvName(env_name=identifier.name)
            self._loaded_envs[identifier.name] = materialized_task

        self._loaded_tasks[identifier] = materialized_task

    def load_all_tasks_in_cond_file(self, rel_cond_file_path: pathlib.Path) -> int:
        """
        Loads all tasks in the specified COND file. Note that
        `rel_cond_file_path` should be a relative path to a COND file (relative
        to the project root). This method will return the number of tasks loaded.
        """
        if rel_cond_file_path not in self._loaded_raw_tasks:
            abs_cond_file_path = self._project_root / rel_cond_file_path
            self._loaded_raw_tasks[rel_cond_file_path] = (
                self._task_loader.parse_cond_file(abs_cond_file_path)
            )

        tasks_loaded = 0
        cond_file_dir = rel_cond_file_path.parent
        for task_name, raw_task in self._loaded_raw_tasks[rel_cond_file_path].items():
            identifier = TaskIdentifier(path=cond_file_dir, name=task_name)
            if identifier in self._loaded_tasks:
                continue
            self._loaded_tasks[identifier] = self._materialize_raw_task(
                identifier, raw_task
            )
            tasks_loaded += 1
        return tasks_loaded

    def load_all_known_tasks(
        self, git: Git
    ) -> List[Tuple[pathlib.Path, int, Optional[ConductorError]]]:
        """
        For Git-tracked projects, this method loads all tasks in all checked-in
        COND files. Note that this method does not validate the task
        dependencies nor does it check for dependency cycles.

        Returns the number of tasks loaded for each COND file and any errors.
        """
        if self._all_loaded:
            return []

        rel_cond_files = [
            pathlib.Path(file_path)
            for file_path in git.find_files([COND_FILE_NAME, f"**/{COND_FILE_NAME}"])
        ]
        load_results: List[Tuple[pathlib.Path, int, Optional[ConductorError]]] = []
        with prevent_module_caching():
            for rel_cond_file in rel_cond_files:
                try:
                    tasks_loaded = self.load_all_tasks_in_cond_file(rel_cond_file)
                    load_results.append((rel_cond_file, tasks_loaded, None))
                except ConductorError as ex:
                    ex.add_file_context(rel_cond_file)
                    load_results.append((rel_cond_file, 0, ex))
            self._all_loaded = True
            return load_results

    def validate_all_loaded_tasks(self) -> List[TaskIdentifier]:
        """
        Validates the loaded tasks by checking that all dependencies exist and
        that there are no cycles. This will also compute the "root" tasks (tasks
        that do not have any dependees).
        """
        visited = set()
        # Keyed by task identifier. Value is the number of dependees.
        root_candidates: Dict[TaskIdentifier, int] = {}

        def do_traversal(root: TaskIdentifier):
            stack = [(root, 0)]
            curr_path: Set[TaskIdentifier] = set()
            while len(stack) > 0:
                curr_id, visit_count = stack.pop()

                if visit_count > 0:
                    # Second visit. We've finished processing this task's children.
                    curr_path.remove(curr_id)
                    continue

                if curr_id in curr_path:
                    # The user's dependency graph contains a cycle
                    raise CyclicDependency(task_identifier=root).add_file_context(
                        root.path_to_cond_file(self._project_root)
                    )

                if curr_id in visited:
                    # We put this check here to be able to detect cyclic
                    # dependencies. If we've already visited this task, we don't
                    # want to visit its children again.
                    continue

                if curr_id not in self._loaded_tasks:
                    # References a dependency that does not exist (or has not
                    # been loaded).
                    raise TaskNotFound(task_identifier=str(curr_id))

                visited.add(curr_id)
                curr_path.add(curr_id)
                stack.append((curr_id, 1))
                curr_task = self._loaded_tasks[curr_id]

                # For runnable tasks, if they reference an environment, make
                # sure it exists.
                if (
                    isinstance(curr_task, RunCommand)
                    or isinstance(curr_task, RunExperiment)
                ) and curr_task.env is not None:
                    if curr_task.env not in self._loaded_tasks:
                        raise EnvNotFound(env_name=curr_task.env.name)
                    env_task = self._loaded_tasks[curr_task.env]
                    if not isinstance(env_task, Environment):
                        raise EnvNotEnv(env_name=curr_task.env.name)

                for dep_id in curr_task.deps:
                    # This task depends on `dep_id`. So `dep_id` has a dependee
                    # and is not a root task.
                    if dep_id in root_candidates:
                        root_candidates[dep_id] += 1
                    stack.append((dep_id, 0))

        for task_id in self._loaded_tasks.keys():
            if task_id in visited:
                continue
            root_candidates[task_id] = 0
            do_traversal(task_id)

        # Check for duplicate envs.
        env_names = set()
        for task in self._loaded_tasks.values():
            if not isinstance(task, Environment):
                continue
            if task.identifier.name in env_names:
                raise DuplicateEnvName(env_name=task.identifier.name)
            env_names.add(task.identifier.name)

        # Return the root tasks.
        return [
            task_id
            for task_id, dependee_count in root_candidates.items()
            if dependee_count == 0
        ]

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
