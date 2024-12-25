import pathlib
import conductor.envs.proto_gen.maestro_pb2_grpc as rpc
import conductor.envs.proto_gen.maestro_pb2 as pb
from conductor.envs.maestro.interface import MaestroInterface, ExecuteTaskType
from conductor.errors import ConductorError, InternalError
from conductor.execution.version_index import Version
from conductor.task_identifier import TaskIdentifier

# pylint: disable=no-member
# See https://github.com/protocolbuffers/protobuf/issues/10372

# pylint: disable=invalid-overridden-method


class MaestroGrpc(rpc.MaestroServicer):
    """
    A shim layer used to implement Maestro's gRPC interface.
    """

    def __init__(self, maestro: MaestroInterface) -> None:
        self._maestro = maestro

    async def UnpackBundle(
        self, request: pb.UnpackBundleRequest, context
    ) -> pb.UnpackBundleResult:
        try:
            bundle_path = pathlib.Path(request.bundle_path)
            workspace_name = await self._maestro.unpack_bundle(bundle_path)
            return pb.UnpackBundleResult(
                response=pb.UnpackBundleResponse(workspace_name=workspace_name)
            )
        except ConductorError as ex:
            return pb.UnpackBundleResult(error=_error_to_pb(ex))

    async def ExecuteTask(
        self, request: pb.ExecuteTaskRequest, context
    ) -> pb.ExecuteTaskResult:
        try:
            workspace_name = request.workspace_name
            project_root = pathlib.Path(request.project_root)
            task_identifier = TaskIdentifier.from_str(request.task_identifier)
            dep_versions = {}
            for dep in request.dep_versions:
                dep_id = TaskIdentifier.from_str(dep.task_identifier)
                dep_ver = dep.version
                version = Version(
                    dep_ver.timestamp,
                    dep_ver.commit_hash,
                    has_uncommitted_changes=False,
                )
                dep_versions[dep_id] = version
            if request.execute_task_type == pb.TT_RUN_EXPERIMENT:
                execute_task_type = ExecuteTaskType.RunExperiment
            elif request.execute_task_type == pb.TT_RUN_COMMAND:
                execute_task_type = ExecuteTaskType.RunCommand
            else:
                raise InternalError(
                    details=f"Unsupported execute task type {str(request.execute_task_type)}."
                )
            response = await self._maestro.execute_task(
                workspace_name,
                project_root,
                task_identifier,
                dep_versions,
                execute_task_type,
            )
            return pb.ExecuteTaskResult(
                response=pb.ExecuteTaskResponse(
                    start_timestamp=response.start_timestamp,
                    end_timestamp=response.end_timestamp,
                )
            )
        except ConductorError as ex:
            return pb.ExecuteTaskResult(error=_error_to_pb(ex))

    async def UnpackTaskOutputs(
        self, request: pb.UnpackTaskOutputsRequest, context
    ) -> pb.UnpackTaskOutputsResult:
        try:
            workspace_name = request.workspace_name
            project_root = pathlib.Path(request.project_root)
            archive_path = pathlib.Path(request.task_archive_path)
            num_unpacked_tasks = await self._maestro.unpack_task_outputs(
                workspace_name, project_root, archive_path
            )
            return pb.UnpackTaskOutputsResult(
                response=pb.UnpackTaskOutputsResponse(
                    num_unpacked_tasks=num_unpacked_tasks
                )
            )
        except ConductorError as ex:
            return pb.UnpackTaskOutputsResult(error=_error_to_pb(ex))

    async def PackTaskOutputs(
        self, request: pb.PackTaskOutputsRequest, context
    ) -> pb.PackTaskOutputsResult:
        try:
            workspace_name = request.workspace_name
            project_root = pathlib.Path(request.project_root)
            versioned_tasks = []
            for task in request.versioned_tasks:
                task_id = TaskIdentifier.from_str(task.task_identifier)
                version = Version(
                    task.version.timestamp,
                    task.version.commit_hash,
                    has_uncommitted_changes=False,
                )
                versioned_tasks.append((task_id, version))
            unversioned_tasks = []
            for task_id_str in request.unversioned_task_identifiers:
                task_id = TaskIdentifier.from_str(task_id_str)
                unversioned_tasks.append(task_id)
            response = await self._maestro.pack_task_outputs(
                workspace_name, project_root, versioned_tasks, unversioned_tasks
            )
            return pb.PackTaskOutputsResult(
                response=pb.PackTaskOutputsResponse(
                    num_packed_tasks=response.num_packed_tasks,
                    task_archive_path=str(response.task_archive_path),
                )
            )
        except ConductorError as ex:
            return pb.PackTaskOutputsResult(error=_error_to_pb(ex))

    async def Shutdown(self, request: pb.ShutdownRequest, context) -> pb.ShutdownResult:
        try:
            response_message = await self._maestro.shutdown(request.key)
            return pb.ShutdownResult(
                response=pb.ShutdownResponse(message=response_message)
            )
        except ConductorError as ex:
            return pb.ShutdownResult(error=_error_to_pb(ex))


def _error_to_pb(ex: ConductorError) -> pb.ConductorError:
    error = pb.ConductorError()
    error.code = ex.error_code
    for kwarg, kwarg_val in ex.kwargs.items():
        msg = error.kwargs.add()
        msg.key = str(kwarg)
        msg.value = str(kwarg_val)

    file_context = ex.file_context
    if file_context is not None:
        error.file_context_path = file_context.file_path
        error.file_context_line_number = file_context.line_number

    if ex.extra_context is not None:
        error.extra_context = ex.extra_context

    return error
