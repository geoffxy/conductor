from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
TT_RUN_COMMAND: ExecuteTaskType
TT_RUN_EXPERIMENT: ExecuteTaskType
TT_UNSPECIFIED: ExecuteTaskType

class ConductorError(_message.Message):
    __slots__ = ["code", "extra_context", "file_context_line_number", "file_context_path", "kwargs"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    EXTRA_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    FILE_CONTEXT_LINE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    FILE_CONTEXT_PATH_FIELD_NUMBER: _ClassVar[int]
    KWARGS_FIELD_NUMBER: _ClassVar[int]
    code: int
    extra_context: str
    file_context_line_number: int
    file_context_path: str
    kwargs: _containers.RepeatedCompositeFieldContainer[ErrorKwarg]
    def __init__(self, code: _Optional[int] = ..., kwargs: _Optional[_Iterable[_Union[ErrorKwarg, _Mapping]]] = ..., file_context_path: _Optional[str] = ..., file_context_line_number: _Optional[int] = ..., extra_context: _Optional[str] = ...) -> None: ...

class ErrorKwarg(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class ExecuteTaskRequest(_message.Message):
    __slots__ = ["dep_versions", "execute_task_type", "project_root", "task_identifier", "workspace_name"]
    DEP_VERSIONS_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_TASK_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ROOT_FIELD_NUMBER: _ClassVar[int]
    TASK_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    dep_versions: _containers.RepeatedCompositeFieldContainer[TaskDependency]
    execute_task_type: ExecuteTaskType
    project_root: str
    task_identifier: str
    workspace_name: str
    def __init__(self, workspace_name: _Optional[str] = ..., project_root: _Optional[str] = ..., task_identifier: _Optional[str] = ..., dep_versions: _Optional[_Iterable[_Union[TaskDependency, _Mapping]]] = ..., execute_task_type: _Optional[_Union[ExecuteTaskType, str]] = ...) -> None: ...

class ExecuteTaskResponse(_message.Message):
    __slots__ = ["end_timestamp", "start_timestamp"]
    END_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    START_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    end_timestamp: int
    start_timestamp: int
    def __init__(self, start_timestamp: _Optional[int] = ..., end_timestamp: _Optional[int] = ...) -> None: ...

class ExecuteTaskResult(_message.Message):
    __slots__ = ["error", "response"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    error: ConductorError
    response: ExecuteTaskResponse
    def __init__(self, response: _Optional[_Union[ExecuteTaskResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...

class ShutdownRequest(_message.Message):
    __slots__ = ["key"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class ShutdownResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class ShutdownResult(_message.Message):
    __slots__ = ["error", "response"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    error: ConductorError
    response: ShutdownResponse
    def __init__(self, response: _Optional[_Union[ShutdownResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...

class TaskDependency(_message.Message):
    __slots__ = ["task_identifier", "version"]
    TASK_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    task_identifier: str
    version: TaskVersion
    def __init__(self, task_identifier: _Optional[str] = ..., version: _Optional[_Union[TaskVersion, _Mapping]] = ...) -> None: ...

class TaskVersion(_message.Message):
    __slots__ = ["commit_hash", "timestamp"]
    COMMIT_HASH_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    commit_hash: str
    timestamp: int
    def __init__(self, timestamp: _Optional[int] = ..., commit_hash: _Optional[str] = ...) -> None: ...

class UnpackBundleRequest(_message.Message):
    __slots__ = ["bundle_path"]
    BUNDLE_PATH_FIELD_NUMBER: _ClassVar[int]
    bundle_path: str
    def __init__(self, bundle_path: _Optional[str] = ...) -> None: ...

class UnpackBundleResponse(_message.Message):
    __slots__ = ["workspace_name"]
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    workspace_name: str
    def __init__(self, workspace_name: _Optional[str] = ...) -> None: ...

class UnpackBundleResult(_message.Message):
    __slots__ = ["error", "response"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    error: ConductorError
    response: UnpackBundleResponse
    def __init__(self, response: _Optional[_Union[UnpackBundleResponse, _Mapping]] = ..., error: _Optional[_Union[ConductorError, _Mapping]] = ...) -> None: ...

class ExecuteTaskType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []  # type: ignore
