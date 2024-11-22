#!/bin/bash

# This script is used to build the Conductor wheel and copy it to the envs
# resources submodule.

set -e

SCRIPT_PATH=$(cd $(dirname $0) && pwd -P)
cd $SCRIPT_PATH
source shared.sh

# 0. Remove the existing wheel so it doesn't get included in the build.
rm -f ../src/conductor/envs/resources/conductor_cli*.whl

# 1. Build the wheel. Note that this will not contain the built wheel. But
# that's intended as Conductor Maestro is not allowed to spawn other Maestro
# instances.
bash build-and-release.sh build

# 2. Copy the wheel to the envs resources submodule.
cp ../dist/conductor_cli*.whl ../src/conductor/envs/resources/
