#!/bin/bash

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "DOWNLOADING DATASET"
echo "====================================="
echo

"$PROJECT_ROOT/scripts/bash/common/install_7zip.sh"
if [ $? -ne 0 ]; then
    echo
    echo "7-ZIP INSTALLATION FAILED"
    exit 1
fi

python3 -u "$PROJECT_ROOT/scripts/python/common/download_dataset.py"
if [ $? -ne 0 ]; then
    echo
    echo "DATASET DOWNLOAD FAILED"
    exit 1
fi

python3 -u "$PROJECT_ROOT/scripts/python/common/extract_dataset.py"
if [ $? -ne 0 ]; then
    echo
    echo "DATASET EXTRACTION FAILED"
    exit 1
fi

echo
echo "====================================="
echo "DATASET READY"
echo "====================================="
echo

exit 0