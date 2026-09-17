"""Add status check constraint to city_projects.

Same reasoning as 0003/0004: city_projects (0002) was created without a
value constraint. app/api/routes_projects.py gives it a real write path.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUSES = ("PLANNED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED")


def upgrade() -> None:
    op.create_check_constraint("ck_city_projects_status", "city_projects", f"status IN {_STATUSES}")


def downgrade() -> None:
    op.drop_constraint("ck_city_projects_status", "city_projects", type_="check")
