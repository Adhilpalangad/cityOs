"""Add image_url (evidence) to incidents.

Spec section 16 lists "Evidence" as an incident field; incidents had no way
to carry one. Nullable, so every existing row is unaffected.

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("image_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "image_url")
