#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING MONGODB TOOLS"
echo "====================================="
echo

ROOT="$PROJECT_ROOT"

echo "[1/2] Installing Terraform..."
bash "$ROOT/scripts/bash/common/install_terraform.sh"

echo
echo "[2/2] Validating Installed Tools..."
bash "$ROOT/scripts/bash/common/validate_tools.sh"

echo
echo "====================================="
echo "MONGODB TOOLS INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0