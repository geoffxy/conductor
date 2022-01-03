#! /bin/bash

SCRIPT_PATH=$(cd $(dirname $0) && pwd -P)
cd $SCRIPT_PATH
source shared.sh
cd ..

set -e

pushd website

if [ "$1" == "--install-deps" ]; then
  npm ci
fi

node_version=$(node --version)

# Build the website.
if [[ "$node_version" =~ ^v17\..+$ ]]; then
  # See https://github.com/webpack/webpack/issues/14532 for details about
  # `--openssl-legacy-provider`.
  NODE_OPTIONS=--openssl-legacy-provider npm run build
else
  npm run build
fi

echo_green "✓ Done"
