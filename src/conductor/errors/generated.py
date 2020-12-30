from .base import ConductorError

# NOTE: This file was generated by errors/codegen.py. Do not edit
#       the generated code unless you know what you are doing!


class TaskParseError(ConductorError):
    error_code = 1000

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "An unknown error occurred when parsing a COND file.".format(

        )


class MissingTaskParameter(ConductorError):
    error_code = 1001

    def __init__(self, **kwargs):
        super().__init__()
        self.parameter_name = kwargs["parameter_name"]
        self.task_type_name = kwargs["task_type_name"]
    
    def _message(self):
        return "Missing parameter '{parameter_name}' for task type '{task_type_name}'.".format(
            parameter_name=self.parameter_name,
            task_type_name=self.task_type_name,
        )


class InvalidTaskParameterType(ConductorError):
    error_code = 1002

    def __init__(self, **kwargs):
        super().__init__()
        self.parameter_name = kwargs["parameter_name"]
        self.task_type_name = kwargs["task_type_name"]
        self.type_name = kwargs["type_name"]
    
    def _message(self):
        return "Invalid type for parameter '{parameter_name}' in task type '{task_type_name}' (expected {type_name}).".format(
            parameter_name=self.parameter_name,
            task_type_name=self.task_type_name,
            type_name=self.type_name,
        )


class UnrecognizedTaskParameters(ConductorError):
    error_code = 1003

    def __init__(self, **kwargs):
        super().__init__()
        self.task_type_name = kwargs["task_type_name"]
    
    def _message(self):
        return "Unrecognized parameter(s) passed to task type '{task_type_name}'.".format(
            task_type_name=self.task_type_name,
        )


class DuplicateTaskName(ConductorError):
    error_code = 1004

    def __init__(self, **kwargs):
        super().__init__()
        self.task_name = kwargs["task_name"]
    
    def _message(self):
        return "Task name '{task_name}' was used more than once.".format(
            task_name=self.task_name,
        )


class InvalidTaskIdentifier(ConductorError):
    error_code = 1005

    def __init__(self, **kwargs):
        super().__init__()
        self.task_identifier = kwargs["task_identifier"]
    
    def _message(self):
        return "Invalid task identifier '{task_identifier}'.".format(
            task_identifier=self.task_identifier,
        )


class InvalidTaskName(ConductorError):
    error_code = 1006

    def __init__(self, **kwargs):
        super().__init__()
        self.task_name = kwargs["task_name"]
    
    def _message(self):
        return "Invalid task name '{task_name}'.".format(
            task_name=self.task_name,
        )


class TaskSyntaxError(ConductorError):
    error_code = 1007

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Encountered a syntax error when parsing a COND file.".format(

        )


class ParsingUnknownNameError(ConductorError):
    error_code = 1008

    def __init__(self, **kwargs):
        super().__init__()
        self.error_message = kwargs["error_message"]
    
    def _message(self):
        return "Encountered an unknown name when parsing a COND file: {error_message}.".format(
            error_message=self.error_message,
        )


class TaskNotFound(ConductorError):
    error_code = 2001

    def __init__(self, **kwargs):
        super().__init__()
        self.task_identifier = kwargs["task_identifier"]
    
    def _message(self):
        return "Task '{task_identifier}' could not be found.".format(
            task_identifier=self.task_identifier,
        )


class MissingProjectRoot(ConductorError):
    error_code = 2002

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Could not locate your project's root. Did you add a .condconfig file?".format(

        )


class CyclicDependency(ConductorError):
    error_code = 2003

    def __init__(self, **kwargs):
        super().__init__()
        self.task_identifier = kwargs["task_identifier"]
    
    def _message(self):
        return "Encountered a cyclic dependency when loading the transitive closure of '{task_identifier}'.".format(
            task_identifier=self.task_identifier,
        )


class TaskNonZeroExit(ConductorError):
    error_code = 3001

    def __init__(self, **kwargs):
        super().__init__()
        self.task_identifier = kwargs["task_identifier"]
        self.code = kwargs["code"]
    
    def _message(self):
        return "Task '{task_identifier}' terminated with a non-zero error code ({code}).".format(
            task_identifier=self.task_identifier,
            code=self.code,
        )


class TaskFailed(ConductorError):
    error_code = 3002

    def __init__(self, **kwargs):
        super().__init__()
        self.task_identifier = kwargs["task_identifier"]
    
    def _message(self):
        return "Task '{task_identifier}' could not be executed.".format(
            task_identifier=self.task_identifier,
        )


__all__ = [
    "TaskParseError",
    "MissingTaskParameter",
    "InvalidTaskParameterType",
    "UnrecognizedTaskParameters",
    "DuplicateTaskName",
    "InvalidTaskIdentifier",
    "InvalidTaskName",
    "TaskSyntaxError",
    "ParsingUnknownNameError",
    "TaskNotFound",
    "MissingProjectRoot",
    "CyclicDependency",
    "TaskNonZeroExit",
    "TaskFailed",
]
