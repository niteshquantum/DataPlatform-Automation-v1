#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING TOOLS"
echo "====================================="
echo

if [ ! -f "$PROJECT_ROOT/tools/terraform/terraform" ]
then
    echo "TERRAFORM NOT FOUND"
    exit 1
fi


echo
echo "Terraform:"
"$PROJECT_ROOT/tools/terraform/terraform" version


echo
echo "====================================="
echo "TOOLS VALIDATED SUCCESSFULLY"
echo "====================================="
echo

exit 0