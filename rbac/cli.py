import os
import sys

sys.path.insert(0, os.getcwd())

import argparse

from rbac.auth import authenticate
from rbac.authorization import has_permission
parser = argparse.ArgumentParser()

parser.add_argument("--username", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--permission", required=True)

args = parser.parse_args()


result = authenticate(
    args.username,
    args.password
)

if not result["authenticated"]:
    print("AUTHENTICATION_FAILED")
    sys.exit(1)

role = result["role"]

if not has_permission(role, args.permission):
    print("ACCESS_DENIED")
    sys.exit(2)

print(f"AUTHORIZED:{role}")
sys.exit(0)