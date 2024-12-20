# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import conductor.envs.proto_gen.maestro_pb2 as maestro__pb2


class MaestroStub(object):
    """Conductor's remote daemon service (Maestro).
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.UnpackBundle = channel.unary_unary(
                '/conductor.Maestro/UnpackBundle',
                request_serializer=maestro__pb2.UnpackBundleRequest.SerializeToString,
                response_deserializer=maestro__pb2.UnpackBundleResult.FromString,
                )
        self.ExecuteTask = channel.unary_unary(
                '/conductor.Maestro/ExecuteTask',
                request_serializer=maestro__pb2.ExecuteTaskRequest.SerializeToString,
                response_deserializer=maestro__pb2.ExecuteTaskResult.FromString,
                )
        self.Shutdown = channel.unary_unary(
                '/conductor.Maestro/Shutdown',
                request_serializer=maestro__pb2.ShutdownRequest.SerializeToString,
                response_deserializer=maestro__pb2.ShutdownResult.FromString,
                )


class MaestroServicer(object):
    """Conductor's remote daemon service (Maestro).
    """

    def UnpackBundle(self, request, context):
        """Used to initialize a repository (workspace) for the current project.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ExecuteTask(self, request, context):
        """Used to execute a Conductor task.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Shutdown(self, request, context):
        """Tell the daemon to shut down.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MaestroServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'UnpackBundle': grpc.unary_unary_rpc_method_handler(
                    servicer.UnpackBundle,
                    request_deserializer=maestro__pb2.UnpackBundleRequest.FromString,
                    response_serializer=maestro__pb2.UnpackBundleResult.SerializeToString,
            ),
            'ExecuteTask': grpc.unary_unary_rpc_method_handler(
                    servicer.ExecuteTask,
                    request_deserializer=maestro__pb2.ExecuteTaskRequest.FromString,
                    response_serializer=maestro__pb2.ExecuteTaskResult.SerializeToString,
            ),
            'Shutdown': grpc.unary_unary_rpc_method_handler(
                    servicer.Shutdown,
                    request_deserializer=maestro__pb2.ShutdownRequest.FromString,
                    response_serializer=maestro__pb2.ShutdownResult.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'conductor.Maestro', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Maestro(object):
    """Conductor's remote daemon service (Maestro).
    """

    @staticmethod
    def UnpackBundle(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/conductor.Maestro/UnpackBundle',
            maestro__pb2.UnpackBundleRequest.SerializeToString,
            maestro__pb2.UnpackBundleResult.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ExecuteTask(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/conductor.Maestro/ExecuteTask',
            maestro__pb2.ExecuteTaskRequest.SerializeToString,
            maestro__pb2.ExecuteTaskResult.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Shutdown(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/conductor.Maestro/Shutdown',
            maestro__pb2.ShutdownRequest.SerializeToString,
            maestro__pb2.ShutdownResult.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
