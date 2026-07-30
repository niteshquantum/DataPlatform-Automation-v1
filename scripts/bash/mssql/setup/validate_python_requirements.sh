#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING MSSQL PYTHON REQUIREMENTS"
echo "====================================="
echo

python3 --version

# Ensure basic system unixodbc is present so pyodbc can bind its libraries successfully
if ! dpkg -l unixodbc 2>/dev/null | grep -q '^ii'
then
    echo "Installing prerequisite system unixodbc library..."
    sudo apt-get update && sudo apt-get install -y unixodbc
fi

python3 -c "import yaml"
python3 -c "import dotenv"
python3 -c "import pyodbc"
python3 -c "import pandas"

echo
echo "====================================="
echo "MSSQL PYTHON REQUIREMENTS VALIDATED"
echo "====================================="
echo

exit 0
