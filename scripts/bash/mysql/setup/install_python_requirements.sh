#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING PYTHON REQUIREMENTS"
echo "====================================="
echo

python3 --version

python3 -m pip install --break-system-packages -r "$PROJECT_ROOT/requirements/mysql.txt"

echo
echo "====================================="
echo "PYTHON REQUIREMENTS INSTALLED"
echo "====================================="
echo

exit 0