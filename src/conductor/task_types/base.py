import pathlib
from typing import Callable, Dict, Sequence, Optional

import conductor.context as c  # pylint: disable=unused-import
import conductor.filename as f
from conductor.task_identifier import TaskIdentifier


class TaskType:
    def __init__(
        self,
        identifier: TaskIdentifier,
        cond_file_path: pathlib.Path,
        deps: Sequence[TaskIdentifier],
    ):
        self._identifier = identifier
        self._cond_file_path = cond_file_path
        # Ensure that the list of deps is immutable by making it a tuple)
        self._deps = tuple(deps)
        self._output_path_suffix = pathlib.Path(
            self.identifier.path, f.task_output_dir(self.identifier)
        )

    def __repr__(self) -> str:
        return "".join(
            [
                self.__class__.__name__,
                "(identifier=",
                str(self._identifier),
            ]
        )

    @staticmethod
    def from_raw_task(
        identifier: TaskIdentifier, raw_task: Dict, deps: Sequence[TaskIdentifier]
    ) -> "TaskType":
        constructor = raw_task["_full_type"]
        del raw_task["name"]
        del raw_task["_full_type"]
        return constructor(identifier=identifier, deps=deps, **raw_task)

    @property
    def identifier(self) -> TaskIdentifier:
        return self._identifier

    @property
    def deps(self) -> Sequence[TaskIdentifier]:
        return self._deps

    @property
    def archivable(self) -> bool:
        return False

    def traverse(self, ctx: "c.Context", visitor: Callable[["TaskType"], None]) -> None:
        """
        Performs a pre-order traversal of the dependency graph starting at
        this task.
        """
        stack = [self.identifier]
        visited = set()

        while len(stack) > 0:
            curr_identifier = stack.pop()
            visited.add(curr_identifier)
            task = ctx.task_index.get_task(curr_identifier)
            visitor(task)
            for dep in task.deps:
                if dep in visited:
                    continue
                stack.append(dep)

    # pylint: disable=unused-argument
    def should_run(self, ctx: "c.Context") -> bool:
        """
        Returns whether or not this task should be executed. If the task
        supports result caching, this method may return `False` to indicate
        that the task does not need to be executed again.
        """
        return True

    def execute(self, ctx: "c.Context") -> None:
        """
        Run this task. This method throws an exception if the task fails.
        """
        raise NotImplementedError

    def get_output_path(
        self,
        ctx: "c.Context",
        create_new: bool = False,  # pylint: disable=unused-argument
    ) -> Optional[pathlib.Path]:
        """
        Returns the absolute path to this task's outputs directory. Note that
        the output path may not exist yet on disk. If the task does not
        support multiple versions, this method will never return `None`.

        If the task supports multiple output versions (e.g.,
        `run_experiment`), this method returns the latest output path. The
        return value will be `None` if no such path exists.

        The `create_new` argument is used by tasks that support multiple
        output versions to indicate that a new output version directory
        should be created. For all other tasks, `create_new` is ignored.
        """
        return ctx.output_path / self._output_path_suffix

    def get_deps_output_paths(self, ctx: "c.Context") -> Sequence[pathlib.Path]:
        """
        Returns a list of `pathlib.Path` objects that represent the latest
        output paths of this task's dependencies.
        """
        deps_output_paths = []
        for dep_identifier in self.deps:
            path = ctx.task_index.get_task(dep_identifier).get_output_path(ctx)
            if path is None:
                continue
            deps_output_paths.append(path)
        return deps_output_paths

    def _get_working_path(self, ctx: "c.Context") -> pathlib.Path:
        return pathlib.Path(ctx.project_root, self._identifier.path)
