

class TaskType:
    def __init__(self, identifier):
        self._identifier = identifier

    def __repr__(self):
        return "".join([
            self.__class__.__name__,
            "(identifier=",
            str(self._identifier),
        ])

    @staticmethod
    def from_raw_task(identifier, raw_task):
        constructor = raw_task["_full_type"]
        del raw_task["name"]
        del raw_task["_full_type"]
        return constructor(identifier=identifier, **raw_task)

    @property
    def identifier(self):
        return self._identifier

    def execute(self):
        raise NotImplementedError
