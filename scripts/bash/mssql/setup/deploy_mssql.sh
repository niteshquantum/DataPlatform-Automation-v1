#!/bin/bash

set -e

# =====================================
# ROOT PATH
# =====================================
source "$(dirname "$0")/../../common/set_project_root.sh"

ROOT="$PROJECT_ROOT"

# =====================================
# TERRAFORM PATH
# =====================================
TF="$ROOT/tools/terraform/terraform"

# =====================================
# CHECK TERRAFORM
# =====================================
if [ ! -f "$TF" ]
then
    echo "Terraform is not installed."
    echo "Run install_tools.sh first."
    exit 1
fi

# =====================================
# CHECK TERRAFORM DIRECTORY
# =====================================
TERRAFORM_DIR="$ROOT/terraform/mssql"

if [ ! -d "$TERRAFORM_DIR" ]
then
    echo "Terraform directory not found."
    echo "$TERRAFORM_DIR"
    exit 1
fi

cd "$TERRAFORM_DIR"

echo
echo "====================================="
echo "TERRAFORM INIT"
echo "====================================="
echo

"$TF" init

echo
echo "====================================="
echo "TERRAFORM VALIDATE"
echo "====================================="
echo

"$TF" validate

echo
echo "====================================="
echo "TERRAFORM APPLY"
echo "====================================="
echo

"$TF" apply \
-target=null_resource.install_mssql_driver_linux \
-target=null_resource.install_mssql_linux \
-target=null_resource.configure_mssql_linux \
-target=null_resource.start_mssql_linux \
-target=null_resource.validate_mssql_linux \
-auto-approve

echo
echo "====================================="
echo "TERRAFORM APPLY COMPLETE"
echo "====================================="
echo

exit 0