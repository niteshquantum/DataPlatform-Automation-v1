import os
import sys

sys.path.insert(0, os.getcwd())

import argparse
from rbac.auth import authenticate

parser = argparse.ArgumentParser()

parser.add_argument("--username", required=True)
parser.add_argument("--password", required=True)

args = parser.parse_args()

result = authenticate(
    args.username,
    args.password
)

if not result["authenticated"]:
    print("AUTHENTICATION_FAILED")
    sys.exit(1)

print(result["role"])
sys.exit(0)