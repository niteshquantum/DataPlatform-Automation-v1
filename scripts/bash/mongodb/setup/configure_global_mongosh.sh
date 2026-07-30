#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_HOST=$(grep "^MONGODB_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

REAL_MONGOSH="$PROJECT_ROOT/databases/mongodb/mongosh/bin/mongosh"
GLOBAL_MONGOSH="/usr/local/bin/mongosh"

echo
echo "====================================="
echo "CONFIGURING GLOBAL MONGOSH COMMAND"
echo "====================================="
echo

if [ ! -f "$REAL_MONGOSH" ]; then
    echo "ERROR: mongosh binary not found"
    echo "Expected: $REAL_MONGOSH"
    exit 1
fi

echo "Creating global mongosh wrapper..."

sudo rm -f "$GLOBAL_MONGOSH"

sudo tee "$GLOBAL_MONGOSH" > /dev/null <<EOF
#!/bin/bash

exec "$REAL_MONGOSH" --host "$MONGODB_HOST" --port "$MONGODB_PORT" "\$@"
EOF

sudo chmod +x "$GLOBAL_MONGOSH"

echo "Validating global mongosh command..."

mongosh --version

echo
echo "====================================="
echo "GLOBAL MONGOSH CONFIGURED SUCCESSFULLY"
echo "====================================="
echo

echo "Command:"
echo "mongosh"

exit 0