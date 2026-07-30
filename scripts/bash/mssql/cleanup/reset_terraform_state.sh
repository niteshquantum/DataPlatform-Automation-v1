#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "RESETTING MSSQL TERRAFORM STATE"
echo "====================================="
echo

TERRAFORM_EXE="$PROJECT_ROOT/tools/terraform/terraform"
TERRAFORM_DIR="$PROJECT_ROOT/terraform/mssql"

echo "Terraform Path      : $TERRAFORM_EXE"
echo "Terraform Directory : $TERRAFORM_DIR"
echo

# =====================================
# VALIDATE TERRAFORM
# =====================================

if [ ! -f "$TERRAFORM_EXE" ]
then
    echo "ERROR: Terraform executable not found:"
    echo "$TERRAFORM_EXE"
    exit 1
fi

if [ ! -d "$TERRAFORM_DIR" ]
then
    echo "ERROR: MSSQL Terraform directory not found:"
    echo "$TERRAFORM_DIR"
    exit 1
fi

# =====================================
# MSSQL LINUX TERRAFORM RESOURCES
# =====================================

LINUX_RESOURCES=(
    "null_resource.validate_mssql_linux"
    "null_resource.start_mssql_linux"
    "null_resource.configure_mssql_linux"
    "null_resource.install_mssql_linux"
    "null_resource.install_mssql_driver_linux"
)

# =====================================
# ENTER TERRAFORM DIRECTORY
# =====================================

cd "$TERRAFORM_DIR"

# =====================================
# CHECK TERRAFORM STATE
# =====================================

if [ ! -f "terraform.tfstate" ]
then

    echo "No Terraform state file found."
    echo "Nothing to reset."
    echo

    echo "====================================="
    echo "MSSQL TERRAFORM STATE RESET SUCCESSFUL"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# READ CURRENT TERRAFORM STATE
# =====================================

echo "Reading current Terraform state..."
echo

STATE_RESOURCES="$("$TERRAFORM_EXE" state list 2>/dev/null || true)"

# =====================================
# HANDLE EMPTY STATE
# =====================================

if [ -z "$STATE_RESOURCES" ]
then

    echo "Terraform state contains no resources."
    echo "Nothing to reset."
    echo

    echo "====================================="
    echo "MSSQL TERRAFORM STATE RESET SUCCESSFUL"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# REMOVE MSSQL LINUX RESOURCES
# =====================================

RESOURCES_FOUND=false

for RESOURCE in "${LINUX_RESOURCES[@]}"
do

    if echo "$STATE_RESOURCES" | grep -Fxq "$RESOURCE"
    then

        RESOURCES_FOUND=true

        echo "Removing Terraform state resource:"
        echo "$RESOURCE"
        echo

        "$TERRAFORM_EXE" state rm "$RESOURCE"

        echo
        echo "Terraform state resource removed successfully."
        echo

    else

        echo "Resource not found in Terraform state:"
        echo "$RESOURCE"
        echo "Skipping."
        echo

    fi

done

# =====================================
# HANDLE NO MATCHING RESOURCES
# =====================================

if [ "$RESOURCES_FOUND" = false ]
then

    echo "No MSSQL Linux resources found in Terraform state."
    echo "Nothing to reset."
    echo

fi

# =====================================
# VALIDATE TERRAFORM STATE RESET
# =====================================

echo "Validating Terraform state cleanup..."
echo

REMAINING_RESOURCES="$("$TERRAFORM_EXE" state list 2>/dev/null || true)"

for RESOURCE in "${LINUX_RESOURCES[@]}"
do

    if echo "$REMAINING_RESOURCES" | grep -Fxq "$RESOURCE"
    then

        echo "ERROR: Terraform resource still exists:"
        echo "$RESOURCE"

        exit 1
    fi

done

echo "MSSQL Linux Terraform resources cleanup validated successfully."

echo
echo "====================================="
echo "MSSQL TERRAFORM STATE RESET SUCCESSFUL"
echo "====================================="
echo

exit 0