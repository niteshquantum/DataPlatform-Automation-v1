#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING MSSQL SERVER AND TOOLS"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

if [ ! -f "$CONFIG_FILE" ]
then
    echo "Configuration file not found."
    echo "Expected: $CONFIG_FILE"
    exit 1
fi

MSSQL_PASSWORD=$(grep "^MSSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PID=$(grep "^MSSQL_PID=" "$CONFIG_FILE" | cut -d'=' -f2)

export DEBIAN_FRONTEND=noninteractive

INSTALL_REQUIRED=false

# =====================================
# CHECK EXISTING INSTALLATION
# =====================================

if [ -x "/opt/mssql/bin/sqlservr" ]
then
    echo "MSSQL Server is already installed."
else
    INSTALL_REQUIRED=true

    echo
    echo "Installing prerequisite packages..."
    echo

    sudo apt-get update

    sudo apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    libldap-2.5-0 

    echo
    echo "Registering Microsoft GPG Key..."
    echo

    if [ ! -f "/usr/share/keyrings/microsoft-prod.gpg" ]
    then
        curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
    else
        echo "Microsoft GPG Key already exists."
    fi

    echo
    echo "Registering SQL Server 2022 Repository..."
    echo
    
    if [ ! -f "/etc/apt/sources.list.d/mssql-server.list" ]
    then
        curl -fsSL https://packages.microsoft.com/config/ubuntu/22.04/prod.list \
        | sudo tee /etc/apt/sources.list.d/microsoft-prod.list >/dev/null
    else
        echo "SQL Server 2022 repository already exists."
    fi
    echo
    echo "Registering Microsoft Product Repository..."
    echo

    if [ ! -f "/etc/apt/sources.list.d/microsoft-prod.list" ]
    then
        curl -fsSL https://packages.microsoft.com/config/ubuntu/24.04/prod.list \
        | sudo tee /etc/apt/sources.list.d/microsoft-prod.list >/dev/null
    else
        echo "Microsoft Product repository already exists."
    fi

    echo
    echo "Updating package index..."
    echo

    sudo apt-get update

    echo
    echo "Installing SQL Server..."
    echo

    sudo apt-get install -y mssql-server

    echo
    echo "Running SQL Server initial setup..."
    echo

    sudo MSSQL_PID="$MSSQL_PID" \
         MSSQL_SA_PASSWORD="$MSSQL_PASSWORD" \
         /opt/mssql/bin/mssql-conf -n setup accept-eula

    echo
    echo "Installing SQL Server Tools..."
    echo

    sudo ACCEPT_EULA=Y apt-get install -y \
        msodbcsql18 \
        mssql-tools18 \
        unixodbc-dev
fi

# =====================================
# SQLCMD LINK
# =====================================

if [ ! -L "/usr/local/bin/sqlcmd" ]
then
    sudo ln -sf /opt/mssql-tools18/bin/sqlcmd /usr/local/bin/sqlcmd
fi

# =====================================
# VALIDATE SQLCMD
# =====================================

if [ ! -x "/opt/mssql-tools18/bin/sqlcmd" ]
then
    echo "sqlcmd installation failed."
    exit 1
fi

echo
echo "Installed SQL Server Version:"
echo "-------------------------------------"
dpkg -s mssql-server | grep Version

echo
echo "Installed sqlcmd Version:"
echo "-------------------------------------"
/opt/mssql-tools18/bin/sqlcmd -? >/dev/null

echo
echo "====================================="
echo "MSSQL SERVER INSTALLATION COMPLETED"
echo "====================================="
echo

exit 0
