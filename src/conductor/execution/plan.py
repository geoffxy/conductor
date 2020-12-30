import time

from conductor.context import Context
from conductor.errors import ConductorError, TaskNotFound
from conductor.task_identifier import TaskIdentifier


class ExecutionPlan:
    def __init__(self, task_identifier: TaskIdentifier):
        # The identifier of the task to run
        self._task_identifier = task_identifier

    def execute(self, ctx: Context):
        """
        Run the execution plan.
        """
        start = time.time()
        try:
            stack = [(ctx.task_index.get_task(self._task_identifier), 0)]
            visited = set()

            while len(stack) > 0:
                next_task, visit_count = stack.pop()
                if visit_count > 0:
                    # All dependencies have finished running, can run now
                    print("Running '{}'...".format(str(next_task.identifier)))
                    next_task.execute(ctx)
                    continue

                visited.add(next_task.identifier)

                # If we do not need to run the task, we do not need to consider
                # its dependencies.
                if not ctx.run_again and not next_task.should_run(ctx):
                    print(
                        "Using cached results for '{}'.".format(
                            str(next_task.identifier)
                        )
                    )
                    continue

                # Process dependencies and then come back to run this task
                stack.append((next_task, 1))
                for dep in next_task.deps:
                    if dep in visited:
                        continue
                    stack.append((ctx.task_index.get_task(dep), 0))
            elapsed = time.time() - start

            # TODO: More robust time formatting
            print("✨ Done! (in {:.2f} seconds)".format(elapsed))

        except TaskNotFound:
            raise AssertionError

        except ConductorError:
            elapsed = time.time() - start
            print("🔴 Task failed. (in {:.2f} seconds)".format(elapsed))
            print()
            raise
