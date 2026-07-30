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

if [ ! -f "$TF" ]; then
    echo "Terraform is not installed."
    echo "Run install_terraform.sh first."
    exit 1
fi

# =====================================
# GO TO MYSQL TERRAFORM
# =====================================

cd "$ROOT/terraform/mysql"

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
-target=null_resource.install_mysql_linux \
-target=null_resource.configure_mysql_linux \
-target=null_resource.start_mysql_linux \
-auto-approve