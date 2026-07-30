"""
RBAC Authorization Module
"""

from rbac.utils import load_json


def get_role_permissions(role):
    """
    Return permissions assigned to a role.
    """

    roles = load_json("roles.json")

    if role not in roles:
        return []

    return roles[role].get("permissions", [])


def has_permission(role, permission):
    """
    Check whether a role has a specific permission.
    """

    permissions = get_role_permissions(role)

    return permission in permissions