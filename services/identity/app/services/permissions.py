from app.db.models import Role
from app.db.seed_data import PERMISSION_CODES, WILDCARD_PERMISSION


def resolve_permissions(role: Role) -> list[str]:
    """Expand a role's granted permission codes, resolving the `*` wildcard."""
    codes = {permission.code for permission in role.permissions}
    if WILDCARD_PERMISSION in codes:
        return list(PERMISSION_CODES)
    return sorted(codes)


def has_permission(granted: list[str], required: str) -> bool:
    return required in granted
