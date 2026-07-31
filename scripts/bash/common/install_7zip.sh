#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING 7-ZIP"
echo "====================================="
echo

if command -v 7z >/dev/null 2>&1; then
    echo "[SUCCESS] 7-Zip already installed."
    echo
    exit 0
fi

echo "[INFO] Installing 7-Zip..."

if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y p7zip-full
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y p7zip p7zip-plugins
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y p7zip p7zip-plugins
else
    echo "[ERROR] Unsupported Linux distribution."
    exit 1
fi

if ! command -v 7z >/dev/null 2>&1; then
    echo "[ERROR] 7-Zip installation failed."
    exit 1
fi

echo
echo "====================================="
echo "7-ZIP INSTALLED"
echo "====================================="
echo

exit 0