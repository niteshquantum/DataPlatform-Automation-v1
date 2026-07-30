#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING MYSQL"
echo "====================================="
echo

if ! command -v mysqld >/dev/null 2>&1
then
    sudo apt-get update
    sudo apt-get install -y mysql-server
fi

echo
echo "MYSQL VERSION"
mysqld --version

echo
echo "MYSQL INSTALLATION COMPLETED"
echo

exit 0