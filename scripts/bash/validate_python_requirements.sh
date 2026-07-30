#!/bin/bash

source "$(dirname "$0")/common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING PYTHON REQUIREMENTS"
echo "====================================="
echo

if ! command -v python3 >/dev/null 2>&1
then
    echo "PYTHON3 NOT FOUND"
    exit 1
fi

echo "Checking mysql-connector-python..."

python3 -c "import mysql.connector"

if [ $? -ne 0 ]
then
    echo "mysql-connector-python NOT INSTALLED"
    exit 1
fi

echo "Checking pandas..."

python3 -c "import pandas"

if [ $? -ne 0 ]
then
    echo "pandas NOT INSTALLED"
    exit 1
fi

echo
echo "====================================="
echo "PYTHON REQUIREMENTS VALIDATED"
echo "====================================="
echo

exit 0