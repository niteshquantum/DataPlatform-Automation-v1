#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGOSH_VERSION=$(grep "^MONGOSH_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "INSTALLING MONGOSH"
echo "====================================="
echo

if [ -d "$PROJECT_ROOT/databases/mongodb/mongosh" ]
then
    echo "mongosh already installed"
    exit 0
fi

mkdir -p "$PROJECT_ROOT/databases/mongodb"

cd "$PROJECT_ROOT/databases/mongodb"

wget -O mongosh.tgz \
"https://downloads.mongodb.com/compass/mongosh-${MONGOSH_VERSION}-linux-x64.tgz"

tar -xzf mongosh.tgz

MONGOSH_FOLDER=$(find . -maxdepth 1 -type d -name "mongosh-*")

mv "$MONGOSH_FOLDER" mongosh

echo
echo "====================================="
echo "MONGOSH INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0