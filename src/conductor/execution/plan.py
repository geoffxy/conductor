from conductor.errors import TaskNotFound


class ExecutionPlan:
    def __init__(self, task_identifier):
        # The identifier of the task to run
        self._task_identifier = task_identifier

    def execute(self, ctx):
        """
        Run the execution plan.
        """
        try:
            stack = [(ctx.task_index.get_task(self._task_identifier), 0)]
            visited = set()

            while len(stack) > 0:
                next_task, visit_count = stack.pop()
                if visit_count > 0:
                    # All dependencies have finished running, can run now
                    print("Running '{}'".format(str(next_task.identifier)))
                    next_task.execute(ctx)
                    continue

                # visit_count == 0, so we need to run the dependencies first
                visited.add(next_task.identifier)
                stack.append((next_task, 1))
                for dep in next_task.deps:
                    if dep in visited:
                        continue
                    stack.append((ctx.task_index.get_task(dep), 0))

        except TaskNotFound:
            raise AssertionError
