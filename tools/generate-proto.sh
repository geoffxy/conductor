#! /bin/bash

SCRIPT_PATH=$(cd $(dirname $0) && pwd -P)
cd $SCRIPT_PATH
source shared.sh

python3 -m grpc_tools.protoc \
  -I../proto \
  --python_out=../src/conductor/envs/proto_gen \
  --pyi_out=../src/conductor/envs/proto_gen \
  --grpc_python_out=../src/conductor/envs/proto_gen \
  ../proto/maestro.proto

# Fix the import path.
sed -i -e "s/import maestro_pb2 as maestro__pb2/import conductor.envs.proto_gen.maestro_pb2 as maestro__pb2/g" ../src/conductor/envs/proto_gen/maestro_pb2_grpc.py
