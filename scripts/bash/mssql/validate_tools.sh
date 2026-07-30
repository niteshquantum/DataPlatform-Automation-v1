#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

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

if [ ! -f "$PROJECT_ROOT/tools/liquibase/liquibase" ]
then
    echo "LIQUIBASE NOT FOUND"
    exit 1
fi

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

MSSQL_DRIVER_VERSION=$(grep "^MSSQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

if [ ! -f "$PROJECT_ROOT/tools/drivers/mssql-jdbc-${MSSQL_DRIVER_VERSION}.jre11.jar" ]
then
    echo "MSSQL DRIVER NOT FOUND"
    exit 1
fi

echo
echo "Terraform:"
"$PROJECT_ROOT/tools/terraform/terraform" version

echo
echo "Liquibase:"
"$PROJECT_ROOT/tools/liquibase/liquibase" --version

echo
echo "====================================="
echo "TOOLS VALIDATED SUCCESSFULLY"
echo "====================================="
echo

exit 0