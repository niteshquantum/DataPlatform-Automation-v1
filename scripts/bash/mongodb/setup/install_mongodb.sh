#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_VERSION=$(grep "^MONGODB_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

MONGODB_DIR="$PROJECT_ROOT/databases/mongodb"
MONGODB_SERVER_DIR="$MONGODB_DIR/server"
MONGOD_BINARY="$MONGODB_SERVER_DIR/bin/mongod"

echo
echo "====================================="
echo "INSTALLING MONGODB"
echo "====================================="
echo

if [ -f "$MONGOD_BINARY" ]; then
    echo "MongoDB already installed"
    echo "Path: $MONGOD_BINARY"
    "$MONGOD_BINARY" --version
    exit 0
fi

echo "Installing MongoDB version: $MONGODB_VERSION"

mkdir -p "$MONGODB_DIR"

cd "$MONGODB_DIR"

rm -f mongodb.tgz
rm -rf "$MONGODB_SERVER_DIR"

wget -O mongodb.tgz \
    "https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2204-${MONGODB_VERSION}.tgz"

tar -xzf mongodb.tgz

MONGODB_FOLDER=$(find . -maxdepth 1 -type d -name "mongodb-linux-*" | head -n 1)

if [ -z "$MONGODB_FOLDER" ]; then
    echo "ERROR: Extracted MongoDB directory not found."
    exit 1
fi

mv "$MONGODB_FOLDER" server

if [ ! -f "$MONGOD_BINARY" ]; then
    echo "ERROR: MongoDB installation failed."
    echo "Expected: $MONGOD_BINARY"
    exit 1
fi

chmod +x "$MONGOD_BINARY"

mkdir -p "$MONGODB_DIR/data"
mkdir -p "$MONGODB_DIR/logs"
mkdir -p "$MONGODB_DIR/config"

echo
echo "====================================="
echo "MONGODB INSTALLED SUCCESSFULLY"
echo "====================================="
echo

"$MONGOD_BINARY" --version

exit 0