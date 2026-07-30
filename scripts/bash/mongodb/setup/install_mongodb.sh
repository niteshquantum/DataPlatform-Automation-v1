#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"


CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_VERSION=$(grep "^MONGODB_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "INSTALLING MONGODB"
echo "====================================="
echo

if [ -d "$PROJECT_ROOT/databases/mongodb/server" ]
then
    echo "MongoDB already installed"

    exit 0
fi

mkdir -p "$PROJECT_ROOT/databases/mongodb"

cd "$PROJECT_ROOT/databases/mongodb"

wget -O mongodb.tgz \
"https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2204-${MONGODB_VERSION}.tgz"

tar -xzf mongodb.tgz

MONGODB_FOLDER=$(find . -maxdepth 1 -type d -name "mongodb-linux-*")

mv "$MONGODB_FOLDER" server

mkdir -p "$PROJECT_ROOT/databases/mongodb/data"
mkdir -p "$PROJECT_ROOT/databases/mongodb/logs"
mkdir -p "$PROJECT_ROOT/databases/mongodb/config"

echo
echo "====================================="
echo "MONGODB INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0