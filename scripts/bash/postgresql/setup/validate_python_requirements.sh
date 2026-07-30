#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING PYTHON REQUIREMENTS"
echo "====================================="
echo

python3 --version

python3 -c "import yaml"
python3 -c "import dotenv"
python3 -c "import psycopg2"
python3 -c "import pandas"

echo
echo "====================================="
echo "PYTHON REQUIREMENTS VALIDATED"
echo "====================================="
echo

exit 0