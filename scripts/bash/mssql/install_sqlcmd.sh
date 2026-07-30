#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING SQLCMD"
echo "====================================="
echo

SQLCMD_PATH="/opt/mssql-tools18/bin/sqlcmd"

if [ -x "$SQLCMD_PATH" ]
then
    echo "sqlcmd already installed"

    "$SQLCMD_PATH" -?

    exit 0
fi

sudo mkdir -p /usr/share/keyrings

curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
| sudo gpg --batch --yes --dearmor \
-o /usr/share/keyrings/microsoft-prod.gpg

UBUNTU_VERSION=$(lsb_release -rs)

curl -fsSL \
"https://packages.microsoft.com/config/ubuntu/${UBUNTU_VERSION}/prod.list" \
| sudo tee /etc/apt/sources.list.d/mssql-tools.list > /dev/null

sudo apt-get update

sudo ACCEPT_EULA=Y apt-get install -y \
mssql-tools18 \
unixodbc-dev

sudo ln -sf /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd

echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' \
| sudo tee /etc/profile.d/mssql-tools.sh > /dev/null

export PATH="$PATH:/opt/mssql-tools18/bin"

if [ ! -x "$SQLCMD_PATH" ]
then
    echo "SQLCMD INSTALLATION FAILED"
    exit 1
fi

"$SQLCMD_PATH" -?

echo
echo "====================================="
echo "SQLCMD INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0