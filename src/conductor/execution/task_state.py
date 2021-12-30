import enum


class TaskState(enum.Enum):
    """
    Used to track the progress of tasks when they are executed.
    """

    # The task is queued to be executed
    QUEUED = 0

    # Skipped executing this task because one or more of its dependencies
    # failed to execute successfully.
    SKIPPED = 1

    # The task was executed successfully.
    SUCCEEDED = 2

    # The task was executed successfully at some prior point in time and its
    # results were cached. As a result, the task was not executed as a part of
    # this Conductor invocation.
    SUCCEEDED_CACHED = 3

    # The task failed when it was executed (non-zero exit code).
    FAILED = 4

    # The task was aborted (will stop executing the rest of the tasks).
    ABORTED = 5

    # States used during preprocessing (see `execution.plan.ExecutionPlan`).
    PREPROCESS_FIRST = 6
    PREPROCESS_SECOND = 7
