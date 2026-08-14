#!/bin/bash
# Resolve the one MSSQL database identity used by every CI stage.
MSSQL_DATABASE="${MSSQL_DATABASE:-$(grep '^MSSQL_DB=' "$PROJECT_ROOT/config/ubuntu/mssql.conf" | cut -d'=' -f2)}"
if [[ ! "$MSSQL_DATABASE" =~ ^[A-Za-z0-9_]+$ ]]; then
    echo "MSSQL_DATABASE_CONFIGURATION_ERROR: invalid database name: $MSSQL_DATABASE" >&2
    exit 1
fi
export MSSQL_DATABASE
export MSSQL_DB="$MSSQL_DATABASE"
echo "MSSQL DATABASE : $MSSQL_DATABASE"
