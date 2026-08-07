#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

DB="$1"
if [ -z "$DB" ]; then
    echo "ERROR: Database type not provided"
    exit 1
fi

BUILD_NUMBER="$2"
if [ -z "$BUILD_NUMBER" ]; then
    echo "ERROR: Build number not provided"
    exit 1
fi

SOURCE_DIR="$PROJECT_ROOT/metadata/$DB"
ARCHIVE_DIR="$PROJECT_ROOT/outputs/schema_test/$DB/build_$BUILD_NUMBER"

echo
echo "====================================="
echo "ARCHIVING METADATA"
echo "====================================="
echo

if [ ! -f "$SOURCE_DIR/schema_registry.json" ]; then
    echo "WARNING: schema_registry.json not found, skipping archive"
    exit 0
fi

mkdir -p "$ARCHIVE_DIR"

cp "$SOURCE_DIR/schema_registry.json" "$ARCHIVE_DIR/schema_registry.json"
cp "$SOURCE_DIR/datatype_registry.json" "$ARCHIVE_DIR/datatype_registry.json"

echo "METADATA ARCHIVED TO $ARCHIVE_DIR"
echo

exit 0
