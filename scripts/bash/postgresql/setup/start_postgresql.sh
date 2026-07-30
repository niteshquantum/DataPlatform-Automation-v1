#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

PORT=$(grep "^POSTGRESQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
VERSION=$(grep "^POSTGRESQL_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "STARTING POSTGRESQL"
echo "====================================="
echo

echo "Using PostgreSQL version: $VERSION"
echo "Using PostgreSQL port: $PORT"

# Verify installation
if [ ! -x "/usr/lib/postgresql/$VERSION/bin/initdb" ]
then
    echo "PostgreSQL $VERSION is not installed"
    exit 1
fi

PG_CONF="/etc/postgresql/$VERSION/main/postgresql.conf"

# Create cluster if it does not exist
if [ ! -f "$PG_CONF" ]
then
    echo "Creating PostgreSQL $VERSION cluster..."

    sudo pg_createcluster "$VERSION" main

    PG_CONF="/etc/postgresql/$VERSION/main/postgresql.conf"
fi

# Update port
sudo sed -i "s/^#\?port = .*/port = $PORT/" "$PG_CONF"

# Restart specific version
sudo pg_ctlcluster "$VERSION" main restart

sleep 5

# Validate port
if ! sudo ss -ltn | grep -q ":$PORT "
then
    echo "PostgreSQL not listening on port $PORT"
    exit 1
fi

echo
echo "PostgreSQL started successfully on port $PORT"
echo

exit 0
