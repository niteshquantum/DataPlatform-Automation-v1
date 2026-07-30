#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "CONFIGURING MYSQL USER"
echo "====================================="
echo

sudo mysql <<EOF
CREATE USER IF NOT EXISTS 'rootuser'@'localhost' IDENTIFIED BY 'root123';
ALTER USER 'rootuser'@'localhost' IDENTIFIED BY 'root123';
GRANT ALL PRIVILEGES ON *.* TO 'rootuser'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF

echo
echo "MYSQL USER CONFIGURED"
echo

exit 0