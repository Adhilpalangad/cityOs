"""Create extended domain tables.

Creates: transit_routes, bus_stops, water_zones, power_substations,
environment_readings, infrastructure_assets, city_projects,
citizen_complaints, workflow_tasks, audit_logs, notifications,
simulation_scenarios, knowledge_documents.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transit_routes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("route_number", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("origin", sa.String(100), nullable=False),
        sa.Column("destination", sa.String(100), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("active_buses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("waypoints", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_transit_routes_route_number", "transit_routes", ["route_number"])

    op.create_table(
        "bus_stops",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("route_code", sa.String(50), nullable=True),
        sa.Column("passenger_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_bus_stops_code", "bus_stops", ["code"])

    op.create_table(
        "water_zones",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("zone_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("capacity_liters", sa.Float(), nullable=False, server_default="1000000.0"),
        sa.Column("consumption_lps", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="NORMAL"),
        sa.Column("leak_risk", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("outages_active", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_water_zones_zone_code", "water_zones", ["zone_code"])

    op.create_table(
        "power_substations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("substation_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("capacity_mw", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("load_mw", sa.Float(), nullable=False, server_default="45.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPERATIONAL"),
        sa.Column("outage_risk", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_power_substations_substation_code", "power_substations", ["substation_code"]
    )

    op.create_table(
        "environment_readings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("zone_code", sa.String(50), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False, server_default="28.0"),
        sa.Column("rainfall_mm", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("humidity_pct", sa.Float(), nullable=False, server_default="65.0"),
        sa.Column("aqi", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("flood_risk", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column(
            "recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_environment_readings_zone_code", "environment_readings", ["zone_code"])

    op.create_table(
        "infrastructure_assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("asset_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column(
            "department_code", sa.String(50), nullable=False, server_default="INFRASTRUCTURE"
        ),
        sa.Column("condition", sa.String(20), nullable=False, server_default="GOOD"),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("next_maintenance", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_infrastructure_assets_asset_code", "infrastructure_assets", ["asset_code"])

    op.create_table(
        "city_projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("department_code", sa.String(50), nullable=False),
        sa.Column("budget", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("spent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("completion_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_city_projects_project_code", "city_projects", ["project_code"])

    op.create_table(
        "citizen_complaints",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("complaint_number", sa.String(30), nullable=False, unique=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="General"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="SUBMITTED"),
        sa.Column("reporter_email", sa.String(150), nullable=True),
        sa.Column("department_code", sa.String(50), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_citizen_complaints_complaint_number", "citizen_complaints", ["complaint_number"]
    )

    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("task_number", sa.String(30), nullable=False, unique=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("department_code", sa.String(50), nullable=False),
        sa.Column("assigned_to", sa.String(150), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_workflow_tasks_task_number", "workflow_tasks", ["task_number"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor", sa.String(150), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_resource", sa.String(150), nullable=False),
        sa.Column("department_code", sa.String(50), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.String(150), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="INFO"),
        sa.Column("target_department", sa.String(50), nullable=True),
        sa.Column("channel", sa.String(30), nullable=False, server_default="IN_APP"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "simulation_scenarios",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scenario_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="CREATED"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_simulation_scenarios_scenario_code", "simulation_scenarios", ["scenario_code"]
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("doc_code", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="POLICY"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("vector_id", sa.String(100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_knowledge_documents_doc_code", "knowledge_documents", ["doc_code"])


def downgrade() -> None:
    op.drop_table("knowledge_documents")
    op.drop_table("simulation_scenarios")
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("workflow_tasks")
    op.drop_table("citizen_complaints")
    op.drop_table("city_projects")
    op.drop_table("infrastructure_assets")
    op.drop_table("environment_readings")
    op.drop_table("power_substations")
    op.drop_table("water_zones")
    op.drop_table("bus_stops")
    op.drop_table("transit_routes")
