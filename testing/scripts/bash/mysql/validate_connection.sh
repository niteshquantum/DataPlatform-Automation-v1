#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

bash scripts/bash/mysql/setup/validate_mysql.sh

exit 0
