#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING PYTHON REQUIREMENTS"
echo "====================================="
echo

python3 --version

# Common requirements
python3 -c "import yaml"
python3 -c "import dotenv"
python3 -c "import pandas"

# MongoDB specific requirement
python3 -c "import pymongo"

echo
echo "====================================="
echo "PYTHON REQUIREMENTS VALIDATED"
echo "====================================="
echo

exit 0