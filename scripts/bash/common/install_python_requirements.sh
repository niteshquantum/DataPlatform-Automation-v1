#!/bin/bash

set -e

echo
echo "====================================="
echo "INSTALLING MONGODB PYTHON PACKAGES"
echo "====================================="
echo

if ! python3 -m pip --version >/dev/null 2>&1
then
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

python3 -m pip install \
    --break-system-packages \
    pymongo \
    pandas

echo
echo "====================================="
echo "PYTHON PACKAGES INSTALLED"
echo "====================================="
echo

exit 0