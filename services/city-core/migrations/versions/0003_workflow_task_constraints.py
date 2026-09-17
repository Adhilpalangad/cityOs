"""Add priority/status check constraints to workflow_tasks.

workflow_tasks (0002) was created without value constraints on `priority`/
`status`, unlike every other domain table (roads, vehicles, incidents, ...).
This backfills the same guarantee now that app/api/routes_workflows.py
gives the table real write paths beyond the self-seed-if-empty GET it had
before -- see app/db/models.py's WORKFLOW_PRIORITIES/WORKFLOW_STATUSES.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
_STATUSES = ("PENDING", "IN_PROGRESS", "ESCALATED", "COMPLETED", "REJECTED")


def upgrade() -> None:
    op.create_check_constraint(
        "ck_workflow_tasks_priority", "workflow_tasks", f"priority IN {_PRIORITIES}"
    )
    op.create_check_constraint(
        "ck_workflow_tasks_status", "workflow_tasks", f"status IN {_STATUSES}"
    )


def downgrade() -> None:
    op.drop_constraint("ck_workflow_tasks_status", "workflow_tasks", type_="check")
    op.drop_constraint("ck_workflow_tasks_priority", "workflow_tasks", type_="check")
