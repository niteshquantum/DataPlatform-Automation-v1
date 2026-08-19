#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGOSH_VERSION=$(grep "^MONGOSH_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

MONGOSH_DIR="$PROJECT_ROOT/databases/mongodb/mongosh"
MONGOSH_BINARY="$MONGOSH_DIR/bin/mongosh"

echo
echo "====================================="
echo "INSTALLING MONGOSH"
echo "====================================="
echo

if [ -f "$MONGOSH_BINARY" ]; then
    echo "mongosh already installed"
    echo "Path: $MONGOSH_BINARY"
    "$MONGOSH_BINARY" --version
    exit 0
fi

echo "Installing mongosh version: $MONGOSH_VERSION"

mkdir -p "$PROJECT_ROOT/databases/mongodb"

cd "$PROJECT_ROOT/databases/mongodb"

rm -f mongosh.tgz
rm -rf mongosh

wget -O mongosh.tgz \
    "https://downloads.mongodb.com/compass/mongosh-${MONGOSH_VERSION}-linux-x64.tgz"

tar -xzf mongosh.tgz

MONGOSH_FOLDER=$(find . -maxdepth 1 -type d -name "mongosh-${MONGOSH_VERSION}-linux-x64" | head -n 1)

if [ -z "$MONGOSH_FOLDER" ]; then
    echo "ERROR: Extracted mongosh directory not found."
    exit 1
fi

mv "$MONGOSH_FOLDER" mongosh

if [ ! -f "$MONGOSH_BINARY" ]; then
    echo "ERROR: mongosh installation failed."
    echo "Expected: $MONGOSH_BINARY"
    exit 1
fi

chmod +x "$MONGOSH_BINARY"

echo
echo "====================================="
echo "MONGOSH INSTALLED SUCCESSFULLY"
echo "====================================="
echo

"$MONGOSH_BINARY" --version

exit 0