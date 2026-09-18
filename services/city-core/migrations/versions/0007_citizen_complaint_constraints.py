"""Add status check constraint to citizen_complaints.

Same reasoning as 0003-0006: citizen_complaints (0002) was created without
a value constraint. app/api/routes_complaints.py's new status-transition
endpoint gives it a real write path.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUSES = ("SUBMITTED", "IN_REVIEW", "ASSIGNED", "RESOLVED", "REJECTED")


def upgrade() -> None:
    op.create_check_constraint(
        "ck_citizen_complaints_status", "citizen_complaints", f"status IN {_STATUSES}"
    )


def downgrade() -> None:
    op.drop_constraint("ck_citizen_complaints_status", "citizen_complaints", type_="check")
