#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING LIQUIBASE"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

LIQUIBASE_VERSION=$(grep "^LIQUIBASE_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

TOOLS_DIR="$PROJECT_ROOT/tools/liquibase"

mkdir -p "$TOOLS_DIR"

if [ -f "$TOOLS_DIR/liquibase" ]
then
    echo "Liquibase already installed"

    "$TOOLS_DIR/liquibase" --version

    exit 0
fi

sudo apt-get update
sudo apt-get install -y wget unzip

wget -O "$PROJECT_ROOT/tools/liquibase.zip" "https://github.com/liquibase/liquibase/releases/download/v${LIQUIBASE_VERSION}/liquibase-${LIQUIBASE_VERSION}.zip"

if [ ! -f "$PROJECT_ROOT/tools/liquibase.zip" ]
then
    echo "LIQUIBASE DOWNLOAD FAILED"
    exit 1
fi

unzip -o "$PROJECT_ROOT/tools/liquibase.zip" -d "$TOOLS_DIR"

chmod +x "$TOOLS_DIR/liquibase"

rm -f "$PROJECT_ROOT/tools/liquibase.zip"

echo
echo "Liquibase Version:"
"$TOOLS_DIR/liquibase" --version

echo
echo "====================================="
echo "LIQUIBASE INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0