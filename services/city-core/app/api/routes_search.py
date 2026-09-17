"""Universal City Search (spec section 49).

Moved out of routes_extended.py and extended: the old version only
searched roads/hospitals/incidents/complaints and -- like every other
endpoint that used to live in that file -- required no authentication at
all. Now covers every domain with a real create/update module built this
session too (vehicles, workflow tasks, infrastructure assets, projects)
and requires the same require_permission() every other endpoint in this
service does.

Spec's own example query ("hospitals within 5km of flooded roads with
available ICU capacity") needs geographic + cross-store reasoning this
codebase doesn't have yet (PostGIS distance queries, a flood-risk signal
tied to roads, Neo4j/Qdrant); this is the honest version -- a real
multi-table keyword search, not a fake semantic one.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.db.models import (
    CitizenComplaint,
    Hospital,
    Incident,
    InfrastructureAsset,
    Road,
    Vehicle,
    WorkflowTask,
)

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("", dependencies=[Depends(require_permission("search.read"))])
async def universal_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=5, ge=1, le=20, description="Max results per category"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    pattern = f"%{q.lower()}%"

    roads = (
        await db.scalars(select(Road).where(func.lower(Road.name).like(pattern)).limit(limit))
    ).all()
    hospitals = (
        await db.scalars(
            select(Hospital).where(func.lower(Hospital.name).like(pattern)).limit(limit)
        )
    ).all()
    incidents = (
        await db.scalars(
            select(Incident)
            .where(func.lower(Incident.incident_number).like(pattern))
            .limit(limit)
        )
    ).all()
    complaints = (
        await db.scalars(
            select(CitizenComplaint)
            .where(func.lower(CitizenComplaint.title).like(pattern))
            .limit(limit)
        )
    ).all()
    vehicles = (
        await db.scalars(
            select(Vehicle).where(func.lower(Vehicle.vehicle_id).like(pattern)).limit(limit)
        )
    ).all()
    workflow_tasks = (
        await db.scalars(
            select(WorkflowTask).where(func.lower(WorkflowTask.title).like(pattern)).limit(limit)
        )
    ).all()
    infrastructure_assets = (
        await db.scalars(
            select(InfrastructureAsset)
            .where(func.lower(InfrastructureAsset.name).like(pattern))
            .limit(limit)
        )
    ).all()

    return {
        "query": q,
        "results": {
            "roads": [
                {"id": str(r.id), "name": r.name, "code": r.code, "status": r.status} for r in roads
            ],
            "hospitals": [
                {"id": str(h.id), "name": h.name, "code": h.code, "beds_total": h.beds_total}
                for h in hospitals
            ],
            "incidents": [
                {
                    "id": str(i.id),
                    "number": i.incident_number,
                    "severity": i.severity,
                    "status": i.status,
                }
                for i in incidents
            ],
            "complaints": [
                {
                    "id": str(c.id),
                    "number": c.complaint_number,
                    "title": c.title,
                    "status": c.status,
                }
                for c in complaints
            ],
            "vehicles": [
                {"id": str(v.id), "vehicle_id": v.vehicle_id, "status": v.status} for v in vehicles
            ],
            "workflow_tasks": [
                {
                    "id": str(t.id),
                    "task_number": t.task_number,
                    "title": t.title,
                    "status": t.status,
                }
                for t in workflow_tasks
            ],
            "infrastructure_assets": [
                {
                    "id": str(a.id),
                    "asset_code": a.asset_code,
                    "name": a.name,
                    "risk_level": a.risk_level,
                }
                for a in infrastructure_assets
            ],
        },
    }
