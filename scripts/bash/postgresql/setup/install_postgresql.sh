#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

POSTGRESQL_VERSION=$(grep "^POSTGRESQL_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "INSTALLING POSTGRESQL $POSTGRESQL_VERSION"
echo "====================================="
echo

# Already installed?
if [ -x "/usr/lib/postgresql/$POSTGRESQL_VERSION/bin/initdb" ]
then
    echo "PostgreSQL $POSTGRESQL_VERSION already installed"
    exit 0
fi

sudo apt-get update

# Add PostgreSQL official repository if needed
if ! apt-cache show "postgresql-$POSTGRESQL_VERSION" >/dev/null 2>&1
then
    echo
    echo "Adding PostgreSQL PGDG repository..."
    echo

    sudo apt-get install -y wget ca-certificates gnupg lsb-release

    sudo install -d /usr/share/postgresql-common/pgdg

    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    | sudo tee /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc >/dev/null

    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] \
http://apt.postgresql.org/pub/repos/apt \
$(lsb_release -cs)-pgdg main" \
    | sudo tee /etc/apt/sources.list.d/pgdg.list

    sudo apt-get update
fi

sudo apt-get install -y \
    postgresql-$POSTGRESQL_VERSION \
    postgresql-client-$POSTGRESQL_VERSION

sudo systemctl enable postgresql

# Verify installation
if [ ! -x "/usr/lib/postgresql/$POSTGRESQL_VERSION/bin/initdb" ]
then
    echo "POSTGRESQL $POSTGRESQL_VERSION INSTALLATION FAILED"
    exit 1
fi

echo
echo "PostgreSQL Version:"
/usr/lib/postgresql/$POSTGRESQL_VERSION/bin/postgres --version

echo
echo "====================================="
echo "POSTGRESQL INSTALLED SUCCESSFULLY"
echo
