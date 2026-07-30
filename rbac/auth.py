"""
RBAC Authentication Module
"""

from rbac.utils import load_json, verify_password


def authenticate(username, password):
    """
    Authenticate user using credentials.json
    """

    credentials = load_json("credentials.json")

    for user in credentials.get("users", []):

        if not user.get("enabled", False):
            continue

        if user["username"] != username:
            continue

        if verify_password(password, user["password"]):
            return {
                "authenticated": True,
                "role": user["role"]
            }

    return {
        "authenticated": False,
        "role": None
    }