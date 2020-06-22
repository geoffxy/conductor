

class ConductorError(RuntimeError):
    def __init__(self, *args):
        super().__init__(*args)


class TaskNotFound(ConductorError):
    def __init__(self, *args):
        super().__init__(*args)


class DuplicateTask(ConductorError):
    def __init__(self, *args):
        super().__init__(*args)


class InvalidTaskArguments(ConductorError):
    def __init__(self, *args):
        super().__init__(*args)


class InvalidTaskIdentifier(ConductorError):
    def __init__(self, task_identifier):
        super().__init__(
            "Invalid task identifier '{}'.".format(task_identifier),
        )
