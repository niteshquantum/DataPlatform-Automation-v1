#!/bin/bash

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING JAVA RUNTIME"
echo "====================================="
echo

if ! command -v java >/dev/null 2>&1
then
    echo "JAVA NOT FOUND"
    exit 1
fi

echo "Java Found:"
which java

java -version

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | grep -oE '[0-9]+' | head -n 1)

if [ "$JAVA_VERSION" -lt 17 ]
then
    echo "JAVA 17 OR HIGHER REQUIRED"
    exit 1
fi

echo
echo "====================================="
echo "JAVA RUNTIME VALIDATED"
echo "====================================="
echo

exit 0