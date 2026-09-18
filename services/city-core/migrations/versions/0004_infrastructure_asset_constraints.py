"""Add condition/risk_level check constraints to infrastructure_assets.

Same reasoning as 0003 for workflow_tasks: infrastructure_assets (0002) was
created without value constraints, unlike every table that has a real write
path. app/api/routes_infrastructure.py gives it one now.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CONDITIONS = ("EXCELLENT", "GOOD", "FAIR", "POOR", "CRITICAL")
_RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def upgrade() -> None:
    op.create_check_constraint(
        "ck_infrastructure_assets_condition",
        "infrastructure_assets",
        f"condition IN {_CONDITIONS}",
    )
    op.create_check_constraint(
        "ck_infrastructure_assets_risk_level",
        "infrastructure_assets",
        f"risk_level IN {_RISK_LEVELS}",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_infrastructure_assets_risk_level", "infrastructure_assets", type_="check"
    )
    op.drop_constraint(
        "ck_infrastructure_assets_condition", "infrastructure_assets", type_="check"
    )
