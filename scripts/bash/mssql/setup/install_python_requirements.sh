#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING MSSQL PYTHON REQUIREMENTS"
echo "====================================="
echo

python3 --version

# Detect Python version to append safely the system-break flag on newer OS versions
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

PIP_FLAGS=""
if (( $(echo "$PYTHON_VERSION >= 3.11" | bc -l) )); then
    PIP_FLAGS="--break-system-packages"
fi

python3 -m pip install $PIP_FLAGS -r "$PROJECT_ROOT/requirements/mssql.txt"

echo
echo "====================================="
echo "MSSQL PYTHON REQUIREMENTS INSTALLED"
echo "====================================="
echo

exit 0
