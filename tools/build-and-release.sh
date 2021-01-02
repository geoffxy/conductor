#!/bin/bash

# This script is used to release a new version of the Skyline CLI.

set -e

function check_build_tools() {
  if [ -z "$(which python3)" ]; then
    echo_red "ERROR: Python 3.8+ (python3) must be installed."
    exit 1
  fi

  if [ -z "$(which pip3)" ]; then
    echo_red "ERROR: Pip for Python 3 (pip3) must be installed."
    exit 1
  fi

  set +e
  $(python3 -c "import pep517" 2> /dev/null > /dev/null)
  pep517_exists=$?
  set -e

  if [ $pep517_exists -ne 0 ]; then
    echo_red "ERROR: The pep517 module (used for building wheels) was not found."
    exit 1
  fi

  echo_green "✓ Build tooling OK"
}

function check_release_tools() {
  if [ -z "$(which twine)" ]; then
    echo_red "ERROR: Twine (used for uploading wheels to PyPI) must be installed."
    exit 1
  fi
  echo_green "✓ Release tooling OK"
}

function build_wheels() {
  pushd ..

  echo_yellow "> Building wheels..."
  rm -rf build dist
  python3 -m pep517.build .
  echo_green "✓ Wheels successfully built"

  popd
}

function make_and_deploy_release() {
  pushd ..

  echo ""
  echo_yellow "> Uploading release to PyPI..."
  twine upload -r pypi "dist/conductor_cli-${NEXT_CLI_VERSION}*"
  echo_green "✓ New release uploaded to PyPI"

  echo ""
  echo_yellow "> Creating a release tag..."
  git tag -a "$VERSION_TAG" -m ""
  git push --follow-tags
  echo_green "✓ Git release tag created and pushed to GitHub"

  popd
}

function get_repo_hash() {
  echo "$(git rev-parse HEAD)"
}

function check_repo_for_release() {
  # Make sure everything has been committed
  if [[ ! -z $(git status --porcelain) ]];
  then
    echo_red "ERROR: There are uncommitted changes. Please commit before releasing."
    exit 1
  fi

  # Make sure we're on master
  MASTER_HASH=$(git rev-parse master)
  CURR_HASH=$(git rev-parse HEAD)

  if [[ $MASTER_HASH != $CURR_HASH ]]; then
    echo_red "ERROR: You must be on master when releasing."
    exit 1
  fi

  echo_green "✓ Repository OK"
}

function build_main() {
  echo ""
  echo_yellow "> Checking build tools..."
  check_build_tools

  echo ""
  echo_yellow "> Build tooling versions:"
  echo "$(python3 --version)"
  echo "$(pip3 --version)"

  echo ""
  build_wheels
}

function release_main() {
  echo ""
  echo_yellow "> Checking the repository..."
  check_repo_for_release

  echo ""
  echo_yellow "> Checking release tools..."
  check_release_tools

  echo ""
  echo_yellow "> Twine version:"
  echo "$(twine --version)"

  NEXT_VERSION=$(cd ../src && python3 -c "import conductor; print(conductor.__version__)")
  VERSION_TAG="v$NEXT_VERSION"
  REPO_HASH=$(get_repo_hash)

  echo ""
  echo_yellow "> This build's version will be '$VERSION_TAG'."
  prompt_yn "> Is this correct? (y/N) "

  build_main

  echo ""
  echo_yellow "> This tool will release the code at commit hash '$REPO_HASH'."
  prompt_yn "> Do you want to continue? This is the final confirmation step. (y/N) "

  echo ""
  echo_yellow "> Releasing $VERSION_TAG..."
  make_and_deploy_release
}

function main() {
  echo ""
  echo_blue "Conductor Build and Release Tool"
  echo_blue "================================"

  if [ "$1" == $build_mode ]; then
    build_main $@
  elif [ "$1" == $release_mode ]; then
    release_main $@
  else
    echo_red "ERROR: Unrecognized mode $1"
    exit 1
  fi

  echo_green "✓ Done!"
}

SCRIPT_PATH=$(cd $(dirname $0) && pwd -P)
cd $SCRIPT_PATH
source shared.sh

build_mode="build"
release_mode="release"

if [ -z $1 ]; then
  echo "Usage $0 <mode> (where <mode> is either '$build_mode' or '$release_mode')."
  echo ""
  echo "build:    Only build the package wheels."
  echo "release:  Build the package wheels and upload them to PyPI."
  exit 1
fi

main $@
