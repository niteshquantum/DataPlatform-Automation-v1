#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING TOOLS"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/validate_tools.sh"

echo
echo "====================================="
echo "TOOLS VALIDATED SUCCESSFULLY"
echo "====================================="
echo

exit 0
