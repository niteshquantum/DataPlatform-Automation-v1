#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

echo
echo "====================================="
echo "STARTING LOCAL MYSQL SETUP PIPELINE"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/install_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/validate_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_java_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/install_tools.sh"

echo
echo "====================================="
echo "CHECKING MYSQL INSTANCE STATE"
echo "====================================="
echo.

INSTANCE_STATE_OUTPUT=$(bash "$PROJECT_ROOT/scripts/bash/mysql/setup/check_instance.sh" || true)

INSTANCE_STATE=$(printf '%s' "$INSTANCE_STATE_OUTPUT" | grep '^INSTANCE_STATE=' | cut -d'=' -f2- | head -n1 || true)

if [ -z "$INSTANCE_STATE" ]; then

    INSTANCE_STATE=UNKNOWN

fi

echo "Instance State: $INSTANCE_STATE"

if [ "$INSTANCE_STATE" = "INSTANCE_RUNNING_AND_USABLE" ]; then

    echo "Reusing existing MySQL instance."

elif [ "$INSTANCE_STATE" = "INSTANCE_INSTALLED_BUT_STOPPED" ]; then

    echo "Starting existing MySQL instance."
    bash "$PROJECT_ROOT/scripts/bash/mysql/setup/start_mysql.sh"

elif [ "$INSTANCE_STATE" = "NO_INSTANCE" ]; then

    echo "Deploying project-local MySQL instance."
    bash "$PROJECT_ROOT/scripts/bash/mysql/setup/deploy_mysql.sh"

    echo "Starting MySQL instance."
    bash "$PROJECT_ROOT/scripts/bash/mysql/setup/start_mysql.sh"

else

    echo "ERROR: Unexpected instance state: $INSTANCE_STATE"
    exit 1

fi

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/validate_environment.sh"

echo
echo "====================================="
echo "MYSQL SETUP SUCCESSFUL"
echo "====================================="
echo

exit 0
