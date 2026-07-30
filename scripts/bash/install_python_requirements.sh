#!/bin/bash

echo
echo "====================================="
echo "INSTALLING PYTHON REQUIREMENTS"
echo "====================================="
echo

python3 -m pip install --upgrade pip

python3 -m pip install -r requirements.txt

echo
echo "====================================="
echo "PYTHON REQUIREMENTS INSTALLED"
echo "====================================="
echo

exit 0