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
    echo "Run install_terraform.sh first."
    exit 1
fi

# =====================================
# GO TO POSTGRESQL TERRAFORM
# =====================================

cd "$ROOT/terraform/postgresql"

echo
echo "====================================="
echo "TERRAFORM INIT"
echo "====================================="
echo

"$TF" init

echo
echo "====================================="
echo "TERRAFORM APPLY"
echo "====================================="
echo

"$TF" apply \
-target=null_resource.install_postgresql_linux \
-target=null_resource.start_postgresql_linux \
-auto-approve

echo
echo "====================================="
echo "POSTGRESQL DEPLOYMENT COMPLETED"
echo "====================================="
echo

exit 0