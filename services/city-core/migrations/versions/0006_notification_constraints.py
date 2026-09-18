"""Add severity/channel check constraints to notifications.

Same reasoning as 0003-0005: notifications (0002) was created without
value constraints. app/api/routes_notifications.py and the new trigger
rules in app/services/notifications.py give it real write paths.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SEVERITIES = ("INFO", "WARNING", "CRITICAL")
_CHANNELS = ("IN_APP", "EMAIL", "SMS", "PUSH")


def upgrade() -> None:
    op.create_check_constraint(
        "ck_notifications_severity", "notifications", f"severity IN {_SEVERITIES}"
    )
    op.create_check_constraint(
        "ck_notifications_channel", "notifications", f"channel IN {_CHANNELS}"
    )


def downgrade() -> None:
    op.drop_constraint("ck_notifications_channel", "notifications", type_="check")
    op.drop_constraint("ck_notifications_severity", "notifications", type_="check")
