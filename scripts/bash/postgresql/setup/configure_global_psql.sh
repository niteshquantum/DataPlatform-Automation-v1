#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

POSTGRESQL_HOST=$(grep "^POSTGRESQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_PORT=$(grep "^POSTGRESQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_DB=$(grep "^POSTGRESQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_USER=$(grep "^POSTGRESQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_PASSWORD=$(grep "^POSTGRESQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_VERSION=$(grep "^POSTGRESQL_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

REAL_PSQL="/usr/lib/postgresql/$POSTGRESQL_VERSION/bin/psql"
GLOBAL_PSQL="/usr/local/bin/psql"

echo
echo "====================================="
echo "CONFIGURING GLOBAL PSQL COMMAND"
echo "====================================="
echo

if [ ! -x "$REAL_PSQL" ]; then
    echo "ERROR: psql binary not found"
    echo "Expected: $REAL_PSQL"
    exit 1
fi

echo "Creating global psql wrapper..."

sudo rm -f "$GLOBAL_PSQL"

sudo tee "$GLOBAL_PSQL" > /dev/null <<EOF
#!/bin/bash

export PGPASSWORD="$POSTGRESQL_PASSWORD"

exec "$REAL_PSQL" \
    --host="$POSTGRESQL_HOST" \
    --port="$POSTGRESQL_PORT" \
    --username="$POSTGRESQL_USER" \
    --dbname="$POSTGRESQL_DB" \
    "\$@"
EOF

sudo chmod +x "$GLOBAL_PSQL"

echo
echo "Validating global psql command..."

psql --version

echo
echo "====================================="
echo "GLOBAL PSQL CONFIGURED SUCCESSFULLY"
echo "====================================="
echo

echo "PostgreSQL connection command:"
echo
echo "psql"
echo

exit 0