#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING TERRAFORM"
echo "====================================="
echo

TOOLS_DIR="$PROJECT_ROOT/tools/terraform"

mkdir -p "$TOOLS_DIR"

if [ -f "$TOOLS_DIR/terraform" ]
then
    chmod +x "$TOOLS_DIR/terraform"

    echo "Terraform already installed"
    "$TOOLS_DIR/terraform" version
    exit 0
fi

sudo apt-get update

sudo apt-get install -y wget unzip

wget -O "$PROJECT_ROOT/tools/terraform.zip" "https://releases.hashicorp.com/terraform/1.13.0/terraform_1.13.0_linux_amd64.zip"

if [ ! -f "$PROJECT_ROOT/tools/terraform.zip" ]
then
    echo "TERRAFORM DOWNLOAD FAILED"
    exit 1
fi

unzip -o "$PROJECT_ROOT/tools/terraform.zip" -d "$TOOLS_DIR"

if [ ! -f "$TOOLS_DIR/terraform" ]
then
    echo "TERRAFORM EXTRACTION FAILED"
    exit 1
fi

chmod +x "$TOOLS_DIR/terraform"

rm -f "$PROJECT_ROOT/tools/terraform.zip"

echo
echo "Terraform Version:"
"$TOOLS_DIR/terraform" version

echo
echo "====================================="
echo "TERRAFORM INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0