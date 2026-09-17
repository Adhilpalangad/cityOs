"""Create roads, hospitals, vehicles, and incidents tables.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("road_type", sa.String(30), nullable=False, server_default="local"),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_vehicle_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_speed_kmh", sa.Float(), nullable=True),
        sa.Column("traffic_level", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("waypoints", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("status IN ('OPEN', 'CLOSED', 'MAINTENANCE')", name="ck_roads_status"),
        sa.CheckConstraint(
            "traffic_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name="ck_roads_traffic_level"
        ),
        sa.CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name="ck_roads_risk_level"
        ),
    )
    op.create_index("ix_roads_code", "roads", ["code"])

    op.create_table(
        "hospitals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("beds_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("beds_occupied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icu_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icu_occupied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emergency_capacity", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPERATIONAL"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('OPERATIONAL', 'LIMITED', 'CLOSED')", name="ck_hospitals_status"
        ),
        sa.CheckConstraint(
            "emergency_capacity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_hospitals_emergency_capacity",
        ),
        sa.CheckConstraint("beds_occupied <= beds_total", name="ck_hospitals_beds_bounds"),
        sa.CheckConstraint("icu_occupied <= icu_total", name="ck_hospitals_icu_bounds"),
    )
    op.create_index("ix_hospitals_code", "hospitals", ["code"])

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("vehicle_id", sa.String(50), nullable=False, unique=True),
        sa.Column("vehicle_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("heading_degrees", sa.Float(), nullable=True),
        sa.Column("position_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "vehicle_type IN ('public_transport', 'ambulance', 'private', 'fleet')",
            name="ck_vehicles_type",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE')", name="ck_vehicles_status"
        ),
    )
    op.create_index("ix_vehicles_vehicle_id", "vehicles", ["vehicle_id"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incident_number", sa.String(30), nullable=False, unique=True),
        sa.Column("incident_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DETECTED"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column(
            "road_id", sa.Uuid(), sa.ForeignKey("roads.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("reporter", sa.String(150), nullable=True),
        sa.Column("department_code", sa.String(50), nullable=True),
        sa.Column("assigned_to", sa.String(150), nullable=True),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "incident_type IN ('ROAD_ACCIDENT', 'FIRE', 'FLOOD', 'MEDICAL_EMERGENCY', "
            "'INFRASTRUCTURE_FAILURE', 'PUBLIC_SAFETY')",
            name="ck_incidents_type",
        ),
        sa.CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name="ck_incidents_severity"
        ),
        sa.CheckConstraint(
            "status IN ('DETECTED', 'VERIFIED', 'ASSIGNED', 'RESPONDING', 'RESOLVED', 'ANALYZED')",
            name="ck_incidents_status",
        ),
    )
    op.create_index("ix_incidents_incident_number", "incidents", ["incident_number"])


def downgrade() -> None:
    op.drop_table("incidents")
    op.drop_table("vehicles")
    op.drop_table("hospitals")
    op.drop_table("roads")
