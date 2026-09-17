"""Seed platform departments, permissions, and roles.

Revision ID: 0002
Revises: 0001

Seed data lives in `app.db.seed_data` (the single source of truth also used
by the application layer). This migration is a point-in-time snapshot of
that module at the time it shipped; changing RBAC defaults later means
adding a new migration, not editing this one.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.db.seed_data import DEPARTMENTS, PERMISSIONS, ROLES, WILDCARD_PERMISSION

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

departments_table = sa.table(
    "departments",
    sa.column("id", sa.Uuid()),
    sa.column("code", sa.String),
    sa.column("name", sa.String),
)
permissions_table = sa.table(
    "permissions",
    sa.column("id", sa.Uuid()),
    sa.column("code", sa.String),
    sa.column("description", sa.String),
)
roles_table = sa.table(
    "roles",
    sa.column("id", sa.Uuid()),
    sa.column("code", sa.String),
    sa.column("name", sa.String),
    sa.column("department_id", sa.Uuid()),
    sa.column("is_platform_role", sa.Boolean),
)
role_permissions_table = sa.table(
    "role_permissions", sa.column("role_id", sa.Uuid()), sa.column("permission_id", sa.Uuid())
)


def upgrade() -> None:
    department_ids = {code: uuid.uuid4() for code, _ in DEPARTMENTS}
    op.bulk_insert(
        departments_table,
        [{"id": department_ids[code], "code": code, "name": name} for code, name in DEPARTMENTS],
    )

    permission_ids = {code: uuid.uuid4() for code, _ in PERMISSIONS}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "description": description}
            for code, description in PERMISSIONS
        ],
    )

    role_ids = {code: uuid.uuid4() for code, *_ in ROLES}
    op.bulk_insert(
        roles_table,
        [
            {
                "id": role_ids[code],
                "code": code,
                "name": name,
                "department_id": department_ids[department_code] if department_code else None,
                "is_platform_role": is_platform_role,
            }
            for code, name, department_code, is_platform_role, _permissions in ROLES
        ],
    )

    role_permission_rows = []
    for code, _name, _department_code, _is_platform_role, permission_codes in ROLES:
        for permission_code in permission_codes:
            if permission_code == WILDCARD_PERMISSION:
                # Super Administrator: grant every seeded permission explicitly
                # so `role_permissions` stays a complete, queryable record
                # even though the app also honours the "*" shorthand.
                role_permission_rows.extend(
                    {"role_id": role_ids[code], "permission_id": pid}
                    for pid in permission_ids.values()
                )
                continue
            role_permission_rows.append(
                {"role_id": role_ids[code], "permission_id": permission_ids[permission_code]}
            )
    op.bulk_insert(role_permissions_table, role_permission_rows)


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM role_permissions"))
    op.execute(sa.text("DELETE FROM roles"))
    op.execute(sa.text("DELETE FROM permissions"))
    op.execute(sa.text("DELETE FROM departments"))
