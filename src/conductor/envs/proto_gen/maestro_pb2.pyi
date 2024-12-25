from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecuteTaskType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TT_UNSPECIFIED: _ClassVar[ExecuteTaskType]
    TT_RUN_EXPERIMENT: _ClassVar[ExecuteTaskType]
    TT_RUN_COMMAND: _ClassVar[ExecuteTaskType]
TT_UNSPECIFIED: ExecuteTaskType
TT_RUN_EXPERIMENT: ExecuteTaskType
TT_RUN_COMMAND: ExecuteTaskType

class ConductorError(_message.Message):
    __slots__ = ("code", "kwargs", "file_context_path", "file_context_line_number", "extra_context")
    CODE_FIELD_NUMBER: _ClassVar[int]
    KWARGS_FIELD_NUMBER: _ClassVar[int]
    FILE_CONTEXT_PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_CONTEXT_LINE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    EXTRA_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    code: int
    kwargs: _containers.RepeatedCompositeFieldContainer[ErrorKwarg]
    file_context_path: str
    file_context_line_number: int
    extra_context: str
    def __init__(self, code: _Optional[int] = ..., kwargs: _Optional[_Iterable[_Union[ErrorKwarg, _Mapping]]] = ..., file_context_path: _Optional[str] = ..., file_context_line_number: _Optional[int] = ..., extra_context: _Optional[str] = ...) -> None: ...

class ErrorKwarg(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class UnpackBundleRequest(_message.Message):
    __slots__ = ("bundle_path",)
    BUNDLE_PATH_FIELD_NUMBER: _ClassVar[int]
    bundle_path: str
    def __init__(self, bundle_path: _Optional[str] = ...) -> None: ...

class UnpackBundleResponse(_message.Message):
    __slots__ = ("workspace_name",)
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    workspace_name: str
    def __init__(self, workspace_name: _Optional[str] = ...) -> None: ...

class UnpackBundleResult(_message.Message):
    __slots__ = ("response", "error")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    response: UnpackBundleResponse
    error: ConductorError
    def __init__(self, response: _Optional[_Union[UnpackBundleResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...

class ExecuteTaskRequest(_message.Message):
    __slots__ = ("workspace_name", "project_root", "task_identifier", "dep_versions", "execute_task_type")
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ROOT_FIELD_NUMBER: _ClassVar[int]
    TASK_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    DEP_VERSIONS_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_TASK_TYPE_FIELD_NUMBER: _ClassVar[int]
    workspace_name: str
    project_root: str
    task_identifier: str
    dep_versions: _containers.RepeatedCompositeFieldContainer[TaskDependency]
    execute_task_type: ExecuteTaskType
    def __init__(self, workspace_name: _Optional[str] = ..., project_root: _Optional[str] = ..., task_identifier: _Optional[str] = ..., dep_versions: _Optional[_Iterable[_Union[TaskDependency, _Mapping]]] = ..., execute_task_type: _Optional[_Union[ExecuteTaskType, str]] = ...) -> None: ...

class TaskDependency(_message.Message):
    __slots__ = ("task_identifier", "version")
    TASK_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    task_identifier: str
    version: TaskVersion
    def __init__(self, task_identifier: _Optional[str] = ..., version: _Optional[_Union[TaskVersion, _Mapping]] = ...) -> None: ...

class TaskVersion(_message.Message):
    __slots__ = ("timestamp", "commit_hash", "has_uncommitted_changes")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    COMMIT_HASH_FIELD_NUMBER: _ClassVar[int]
    HAS_UNCOMMITTED_CHANGES_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    commit_hash: str
    has_uncommitted_changes: bool
    def __init__(self, timestamp: _Optional[int] = ..., commit_hash: _Optional[str] = ..., has_uncommitted_changes: bool = ...) -> None: ...

class TaskWithVersion(_message.Message):
    __slots__ = ("task_identifier", "version")
    TASK_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    task_identifier: str
    version: TaskVersion
    def __init__(self, task_identifier: _Optional[str] = ..., version: _Optional[_Union[TaskVersion, _Mapping]] = ...) -> None: ...

class ExecuteTaskResponse(_message.Message):
    __slots__ = ("start_timestamp", "end_timestamp", "result_version")
    START_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    END_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    RESULT_VERSION_FIELD_NUMBER: _ClassVar[int]
    start_timestamp: int
    end_timestamp: int
    result_version: TaskVersion
    def __init__(self, start_timestamp: _Optional[int] = ..., end_timestamp: _Optional[int] = ..., result_version: _Optional[_Union[TaskVersion, _Mapping]] = ...) -> None: ...

class ExecuteTaskResult(_message.Message):
    __slots__ = ("response", "error")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    response: ExecuteTaskResponse
    error: ConductorError
    def __init__(self, response: _Optional[_Union[ExecuteTaskResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...

class UnpackTaskOutputsRequest(_message.Message):
    __slots__ = ("workspace_name", "project_root", "task_archive_path")
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ROOT_FIELD_NUMBER: _ClassVar[int]
    TASK_ARCHIVE_PATH_FIELD_NUMBER: _ClassVar[int]
    workspace_name: str
    project_root: str
    task_archive_path: str
    def __init__(self, workspace_name: _Optional[str] = ..., project_root: _Optional[str] = ..., task_archive_path: _Optional[str] = ...) -> None: ...

class UnpackTaskOutputsResult(_message.Message):
    __slots__ = ("response", "error")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    response: UnpackTaskOutputsResponse
    error: ConductorError
    def __init__(self, response: _Optional[_Union[UnpackTaskOutputsResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...

class UnpackTaskOutputsResponse(_message.Message):
    __slots__ = ("num_unpacked_tasks",)
    NUM_UNPACKED_TASKS_FIELD_NUMBER: _ClassVar[int]
    num_unpacked_tasks: int
    def __init__(self, num_unpacked_tasks: _Optional[int] = ...) -> None: ...

class PackTaskOutputsRequest(_message.Message):
    __slots__ = ("workspace_name", "project_root", "versioned_tasks", "unversioned_task_identifiers")
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ROOT_FIELD_NUMBER: _ClassVar[int]
    VERSIONED_TASKS_FIELD_NUMBER: _ClassVar[int]
    UNVERSIONED_TASK_IDENTIFIERS_FIELD_NUMBER: _ClassVar[int]
    workspace_name: str
    project_root: str
    versioned_tasks: _containers.RepeatedCompositeFieldContainer[TaskWithVersion]
    unversioned_task_identifiers: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, workspace_name: _Optional[str] = ..., project_root: _Optional[str] = ..., versioned_tasks: _Optional[_Iterable[_Union[TaskWithVersion, _Mapping]]] = ..., unversioned_task_identifiers: _Optional[_Iterable[str]] = ...) -> None: ...

class PackTaskOutputsResult(_message.Message):
    __slots__ = ("response", "error")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    response: PackTaskOutputsResponse
    error: ConductorError
    def __init__(self, response: _Optional[_Union[PackTaskOutputsResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...

class PackTaskOutputsResponse(_message.Message):
    __slots__ = ("num_packed_tasks", "task_archive_path")
    NUM_PACKED_TASKS_FIELD_NUMBER: _ClassVar[int]
    TASK_ARCHIVE_PATH_FIELD_NUMBER: _ClassVar[int]
    num_packed_tasks: int
    task_archive_path: str
    def __init__(self, num_packed_tasks: _Optional[int] = ..., task_archive_path: _Optional[str] = ...) -> None: ...

class ShutdownRequest(_message.Message):
    __slots__ = ("key",)
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class ShutdownResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class ShutdownResult(_message.Message):
    __slots__ = ("response", "error")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    response: ShutdownResponse
    error: ConductorError
    def __init__(self, response: _Optional[_Union[ShutdownResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...
