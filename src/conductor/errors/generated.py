from .base import ConductorError

# NOTE: This file was generated by errors/codegen.py. Do not edit
#       the generated code unless you know what you are doing!

# pylint: skip-file


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


class MissingCondFile(ConductorError):
    error_code = 1009

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Could not find a required COND file. Please ensure that you have defined all the tasks that you use.".format(

        )


class DuplicateDependency(ConductorError):
    error_code = 1010

    def __init__(self, **kwargs):
        super().__init__()
        self.task_identifier = kwargs["task_identifier"]
        self.dep_identifier = kwargs["dep_identifier"]
    
    def _message(self):
        return "Task '{task_identifier}' has declared a dependency on '{dep_identifier}' more than once.".format(
            task_identifier=self.task_identifier,
            dep_identifier=self.dep_identifier,
        )


class CombineDuplicateDepName(ConductorError):
    error_code = 1011

    def __init__(self, **kwargs):
        super().__init__()
        self.task_identifier = kwargs["task_identifier"]
        self.task_name = kwargs["task_name"]
    
    def _message(self):
        return "The combine() task '{task_identifier}' has two or more dependencies that share the same task name '{task_name}'. A combine() task's dependencies must have unique names.".format(
            task_identifier=self.task_identifier,
            task_name=self.task_name,
        )


class RunOptionsNonStringKey(ConductorError):
    error_code = 1012

    def __init__(self, **kwargs):
        super().__init__()
        self.identifier = kwargs["identifier"]
    
    def _message(self):
        return "Encountered a non-string option key when processing task '{identifier}'. All option keys must be strings.".format(
            identifier=self.identifier,
        )


class RunOptionsNonPrimitiveValue(ConductorError):
    error_code = 1013

    def __init__(self, **kwargs):
        super().__init__()
        self.key = kwargs["key"]
        self.identifier = kwargs["identifier"]
    
    def _message(self):
        return "Encountered a non-primitive option value for key '{key}' when processing task '{identifier}'. All option values must be either a string, integer, floating point number, or boolean.".format(
            key=self.key,
            identifier=self.identifier,
        )


class ExperimentGroupDuplicateName(ConductorError):
    error_code = 1014

    def __init__(self, **kwargs):
        super().__init__()
        self.instance_name = kwargs["instance_name"]
        self.task_name = kwargs["task_name"]
    
    def _message(self):
        return "Encountered a duplicate experiment instance name '{instance_name}' when processing a run_experiment_group() task with name '{task_name}'. Experiment instance names must be unique.".format(
            instance_name=self.instance_name,
            task_name=self.task_name,
        )


class ExperimentGroupInvalidExperimentInstance(ConductorError):
    error_code = 1015

    def __init__(self, **kwargs):
        super().__init__()
        self.task_name = kwargs["task_name"]
    
    def _message(self):
        return "Encountered an experiment instance that was incorrectly formed when processing a run_experiment_group() task with name '{task_name}'. Experiments in an experiment group must be defined using an iterable of ExperimentInstance named tuples.".format(
            task_name=self.task_name,
        )


class RunArgumentsNonPrimitiveValue(ConductorError):
    error_code = 1016

    def __init__(self, **kwargs):
        super().__init__()
        self.identifier = kwargs["identifier"]
    
    def _message(self):
        return "Encountered a non-primitive argument when processing task '{identifier}'. All arguments must be either a string, integer, floating point number, or boolean.".format(
            identifier=self.identifier,
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
        return "Could not locate your project's root. Did you add a cond_config.toml file?".format(

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


class UnsupportedVersionIndexFormat(ConductorError):
    error_code = 2004

    def __init__(self, **kwargs):
        super().__init__()
        self.version = kwargs["version"]
    
    def _message(self):
        return "Detected an unsupported version index ({version}). Please make sure that you are using the latest version of Conductor.".format(
            version=self.version,
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


class OutputDirTaken(ConductorError):
    error_code = 3003

    def __init__(self, **kwargs):
        super().__init__()
        self.output_dir = kwargs["output_dir"]
    
    def _message(self):
        return "Conductor cannot create its output directory '{output_dir}' because it already exists as a file.".format(
            output_dir=self.output_dir,
        )


class ConductorAbort(ConductorError):
    error_code = 3004

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Conductor's execution has been aborted by the user.".format(

        )


class OutputFileExists(ConductorError):
    error_code = 4001

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "The provided output path points to an existing file. Conductor will not overwrite existing files.".format(

        )


class OutputPathDoesNotExist(ConductorError):
    error_code = 4002

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "The provided output path does not exist. Make sure to create any missing directories.".format(

        )


class NoTaskOutputsToArchive(ConductorError):
    error_code = 4003

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "There are no task outputs to archive. Make sure that you have `cond run` your task at least once and that it (or its dependencies) are archivable.".format(

        )


class CreateArchiveFailed(ConductorError):
    error_code = 4004

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Conductor failed to create an archive.".format(

        )


class ArchiveFileInvalid(ConductorError):
    error_code = 4005

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "The provided archive file does not exist or is corrupted.".format(

        )


class DuplicateTaskOutput(ConductorError):
    error_code = 4006

    def __init__(self, **kwargs):
        super().__init__()
        self.output_dir = kwargs["output_dir"]
    
    def _message(self):
        return "The provided archive contains task output(s) that already exist in the output directory '{output_dir}'.".format(
            output_dir=self.output_dir,
        )


class ConfigParseError(ConductorError):
    error_code = 5001

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Conductor failed to parse cond_config.toml.".format(

        )


class ConfigInvalidValue(ConductorError):
    error_code = 5002

    def __init__(self, **kwargs):
        super().__init__()
        self.config_key = kwargs["config_key"]
    
    def _message(self):
        return "Encountered an invalid value for '{config_key}' in cond_config.toml.".format(
            config_key=self.config_key,
        )


class UnsupportedPlatform(ConductorError):
    error_code = 5003

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Conductor is not supported on your system. Conductor only supports Linux and macOS.".format(

        )


class InvalidJobsCount(ConductorError):
    error_code = 5004

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "The maximum number of parallel jobs must be at least 1.".format(

        )


class CannotSelectJobCount(ConductorError):
    error_code = 5005

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Conductor could not automatically set the maximum number of parallel jobs. Please explicitly specify a number using the --jobs flag.".format(

        )


class CannotSetAgainAndThisCommit(ConductorError):
    error_code = 5006

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "You cannot set both the --again and --this-commit flags.".format(

        )


class ThisCommitUnsupported(ConductorError):
    error_code = 5007

    def __init__(self, **kwargs):
        super().__init__()

    
    def _message(self):
        return "Your project does not use Git or Git integration has been disabled. You cannot use the --this-commit flag when Git is disabled.".format(

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
    "MissingCondFile",
    "DuplicateDependency",
    "CombineDuplicateDepName",
    "RunOptionsNonStringKey",
    "RunOptionsNonPrimitiveValue",
    "ExperimentGroupDuplicateName",
    "ExperimentGroupInvalidExperimentInstance",
    "RunArgumentsNonPrimitiveValue",
    "TaskNotFound",
    "MissingProjectRoot",
    "CyclicDependency",
    "UnsupportedVersionIndexFormat",
    "TaskNonZeroExit",
    "TaskFailed",
    "OutputDirTaken",
    "ConductorAbort",
    "OutputFileExists",
    "OutputPathDoesNotExist",
    "NoTaskOutputsToArchive",
    "CreateArchiveFailed",
    "ArchiveFileInvalid",
    "DuplicateTaskOutput",
    "ConfigParseError",
    "ConfigInvalidValue",
    "UnsupportedPlatform",
    "InvalidJobsCount",
    "CannotSelectJobCount",
    "CannotSetAgainAndThisCommit",
    "ThisCommitUnsupported",
]
