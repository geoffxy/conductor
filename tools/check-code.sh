#! /bin/bash

SCRIPT_PATH=$(cd $(dirname $0) && pwd -P)
cd $SCRIPT_PATH
source shared.sh
cd ..

set -e

echo_blue "Tool Versions"
echo_blue "============="
black --version
mypy --version
pylint --version
echo ""

set +e

echo_blue "Check Formatting (black)"
echo_blue "========================"
black --check .
black_exit=$?
echo ""

echo_blue "Lint (pylint)"
echo_blue "============="
pylint src/conductor errors/codegen.py setup.py
pylint_exit=$?
echo ""

echo_blue "Type Check (mypy)"
echo_blue "================="
mypy src/conductor/__main__.py
mypy_exit=$?
echo ""

function report_status() {
  if [ $1 -eq 0 ]; then
    echo_green "✓ Passed"
  else
    echo_red "✗ Failed"
  fi
}

echo_blue "Results Summary"
echo_blue "==============="
echo -n "Formatting  "; report_status $black_exit
echo -n "Lint        "; report_status $pylint_exit
echo -n "Type Check  "; report_status $mypy_exit

if [ $black_exit -ne 0 ] || [ $pylint_exit -ne 0 ] || [ $mypy_exit -ne 0 ]; then
  exit 1
fi
