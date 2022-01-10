#!/bin/bash

# This script is used to deploy the Conductor website.
#
# Compiled versions of the Conductor website are stored in the `gh-pages` branch
# in this repository. Users need to clone a copy of this repository and switch
# to the `gh-pages` branch and pass in a path to it when running this tool.

set -e

function print_usage() {
  echo "Usage: $0 path/to/deploy/repository"
  echo ""
  echo "This tool is used to deploy the Conductor website."
}

function get_repo_hash() {
  echo "$(git rev-parse HEAD)"
}

function get_repo_short_hash() {
  echo "$(git rev-parse --short HEAD)"
}

function check_repo() {
  # Make sure everything has been committed
  if [[ ! -z $(git status --porcelain) ]];
  then
    echo_red "ERROR: There are uncommitted changes. Please commit before releasing."
    exit 1
  fi

  # Make sure we're on master
  master_hash=$(git rev-parse master)
  curr_hash=$(git rev-parse HEAD)

  if [[ $master_hash != $curr_hash ]]; then
    echo_red "ERROR: You must be on master when deploying."
    exit 1
  fi

  echo_green "✓ Repository OK"
}

function check_deploy_repo() {
  pushd "$DEPLOY_REPO"

  if [[ ! -z $(git status --porcelain) ]];
  then
    echo_red "ERROR: There are uncommitted changes in the website deploy repository. Please remove these files before deploying."
    exit 1
  fi

  # Make sure we're on gh-pages
  deploy_branch_hash=$(git rev-parse gh-pages)
  deploy_hash=$(git rev-parse HEAD)

  if [[ $deploy_branch_hash != $deploy_hash ]]; then
    echo_red "ERROR: The deploy repository copy must be on gh-pages when deploying."
    exit 1
  fi

  popd

  echo_green "✓ Deploy repository OK"
}

function build_website() {
  pushd ../website
  node_version=$(node --version)
  # Build the website.
  if [[ "$node_version" =~ ^v17\..+$ ]]; then
    # See https://github.com/webpack/webpack/issues/14532 for details about
    # `--openssl-legacy-provider`.
    NODE_OPTIONS=--openssl-legacy-provider npm run build
  else
    npm run build
  fi
  rm -f build/.DS_Store
  echo_green "✓ Website build succeeded"
  popd
}

function perform_deploy() {
  # Delete everything to the deploy repository
  pushd "$DEPLOY_REPO"
  rm -rf *
  popd

  # Move over the newly built website
  cp -r ../website/build/* $DEPLOY_REPO

  pushd "$DEPLOY_REPO"

  git add .
  git commit -F- <<EOF
Deploy website at commit $SHORT_HASH

This deployment includes the website files up to commit $MAIN_HASH.
EOF
  echo_green "✓ Deploy repository files updated"

  git push origin gh-pages
  echo_green "✓ Website deployed"

  popd
}

function main() {
  if [ -z "$(which node)" ]; then
    echo_red "ERROR: Node.js (node) must be installed."
    exit 1
  fi

  if [ -z "$(which npm)" ]; then
    echo_red "ERROR: npm must be installed."
    exit 1
  fi

  echo ""
  echo_blue "Conductor Website Deploy Tool"
  echo_blue "============================="

  echo ""
  echo_yellow "> Checking this repository..."
  check_repo

  echo ""
  echo_yellow "> Checking the deploy repository copy..."
  check_deploy_repo

  echo ""
  echo_yellow "> Tooling versions:"
  echo "npm:  $(npm -v)"
  echo "node: $(node -v)"

  MAIN_HASH="$(get_repo_hash)"
  SHORT_HASH="$(get_repo_short_hash)"

  echo ""
  echo_yellow "> This tool will deploy the website code at commit hash '$MAIN_HASH'."
  prompt_yn "> Do you want to continue? This is the final confirmation step. (y/N) "

  echo ""
  echo_yellow "> Building the website..."
  build_website

  echo ""
  echo_yellow "> Deploying the website..."
  perform_deploy

  echo_green "✓ Done!"
}

THIS_SCRIPT_PATH=$(cd $(dirname $0) && pwd -P)
source $THIS_SCRIPT_PATH/shared.sh

DEPLOY_REPO=$1
if [ -z $1 ]; then
  echo_red "ERROR: Please provide a path to the deploy repository."
  echo ""
  print_usage $@
  exit 1
fi

if [ ! -d "$DEPLOY_REPO" ]; then
  echo_red "ERROR: The deploy repository path does not exist."
  exit 1
fi

DEPLOY_REPO=$(cd "$DEPLOY_REPO" && pwd)
cd $THIS_SCRIPT_PATH

main $@
