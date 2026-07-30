#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

MONGOD_BINARY="$PROJECT_ROOT/databases/mongodb/server/bin/mongod"
DATA_DIR="$PROJECT_ROOT/databases/mongodb/data"
LOG_DIR="$PROJECT_ROOT/databases/mongodb/logs"
LOG_FILE="$LOG_DIR/mongod.log"

SERVICE_FILE="/etc/systemd/system/mongodb-automation.service"

echo
echo "====================================="
echo "CONFIGURING MONGODB SYSTEMD SERVICE"
echo "====================================="
echo

if [ ! -f "$MONGOD_BINARY" ]; then
    echo "ERROR: MongoDB binary not found"
    echo "Expected: $MONGOD_BINARY"
    exit 1
fi

mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

echo "Stopping existing MongoDB process if running..."

if ss -ltn | grep -q ":$MONGODB_PORT "; then
    PID=$(lsof -t -i:"$MONGODB_PORT" || true)

    if [ -n "$PID" ]; then
        kill "$PID" || true
        sleep 3
    fi
fi

echo "Creating systemd service..."

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=MongoDB Automation Service
After=network.target

[Service]
Type=simple

ExecStart=$MONGOD_BINARY \
--dbpath $DATA_DIR \
--logpath $LOG_FILE \
--port $MONGODB_PORT

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd..."

sudo systemctl daemon-reload

echo "Enabling MongoDB service..."

sudo systemctl enable mongodb-automation.service

echo "Starting MongoDB service..."

sudo systemctl restart mongodb-automation.service

sleep 5

echo
echo "Validating MongoDB service..."

if ! sudo systemctl is-active --quiet mongodb-automation.service; then
    echo "ERROR: MongoDB service failed to start"

    sudo systemctl status mongodb-automation.service \
        --no-pager || true

    exit 1
fi

echo
echo "====================================="
echo "MONGODB SYSTEMD SERVICE CONFIGURED"
echo "====================================="
echo

sudo systemctl status mongodb-automation.service \
    --no-pager

exit 0