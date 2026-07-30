#!/bin/bash

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING PYTHON RUNTIME"
echo "====================================="
echo

if ! command -v python3 >/dev/null 2>&1
then
    echo "PYTHON3 NOT FOUND"
    exit 1
fi

echo "Python Found:"
which python3

python3 --version

echo
echo "====================================="
echo "PYTHON RUNTIME VALIDATED"
echo "====================================="
echo

exit 0