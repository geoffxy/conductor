from conductor.errors import TaskNotFound


class ExecutionPlan:
    def __init__(self, task_identifier, task_index):
        # The identifier of the task to run
        self._task_identifier = task_identifier
        # A reference to a task index containing the transitive closure of the
        # `task`'s dependencies
        self._task_index = task_index

    def execute(self, project_root):
        """
        Run the execution plan.
        """
        try:
            stack = [(self._task_index.get_task(self._task_identifier), 0)]
            visited = set()

            while len(stack) > 0:
                next_task, visit_count = stack.pop()
                if visit_count > 0:
                    # All dependencies have finished running, can run now
                    print("Running '{}'".format(str(next_task.identifier)))
                    next_task.execute(project_root)
                    continue

                # visit_count == 0, so we need to run the dependencies first
                visited.add(next_task.identifier)
                stack.append((next_task, 1))
                for dep in next_task.deps:
                    if dep in visited:
                        continue
                    stack.append((self._task_index.get_task(dep), 0))

        except TaskNotFound:
            raise AssertionError
