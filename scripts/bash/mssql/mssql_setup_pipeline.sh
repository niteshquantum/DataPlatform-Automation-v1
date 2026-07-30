#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

echo
echo "====================================="
echo "STARTING LOCAL MSSQL SETUP PIPELINE"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/install_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_java_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/install_tools.sh"

echo
echo "====================================="
echo "CHECKING MSSQL INSTANCE STATE"
echo "====================================="
echo

INSTANCE_STATE=$(bash "$PROJECT_ROOT/scripts/bash/mssql/setup/check_instance.sh" || true)

echo "Instance State: $INSTANCE_STATE"

if [ "$INSTANCE_STATE" = "INSTANCE_RUNNING_AND_USABLE" ]; then

    echo "Reusing existing MSSQL instance."

elif [ "$INSTANCE_STATE" = "INSTANCE_INSTALLED_BUT_STOPPED" ]; then

    echo "Starting existing MSSQL instance."
    bash "$PROJECT_ROOT/scripts/bash/mssql/setup/start_mssql.sh"

elif [ "$INSTANCE_STATE" = "NO_INSTANCE" ]; then

    echo "Deploying project-local MSSQL instance."
    bash "$PROJECT_ROOT/scripts/bash/mssql/setup/deploy_mssql.sh"

else

    echo "ERROR: Unexpected instance state: $INSTANCE_STATE"
    exit 1

fi

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_mssql.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_environment.sh"

echo
echo "====================================="
echo "MSSQL SETUP SUCCESSFUL"
echo "====================================="
echo

exit 0
