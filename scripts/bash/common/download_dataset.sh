#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "DOWNLOADING DATASET"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/common/download_dataset.py"

python3 "$PROJECT_ROOT/scripts/python/common/extract_dataset.py"

echo
echo "====================================="
echo "DATASET READY"
echo "====================================="
echo

exit 0