"""Writes AuditLog rows for sensitive actions (spec section 50).

Not wired into every mutation in the system -- only the actions the spec's
own worked example calls sensitive (incident assignment/resolution, road
status changes closing/reopening a road). Before this module existed, the
only AuditLog rows ever created were two hardcoded examples seeded once by
`app/api/routes_extended.py`'s GET /api/v1/audit on first call -- nothing
in the system actually wrote an entry when a real action happened.

Like app/services/incidents.py and app/services/live_ingest.py, this module
doesn't own the DB session or commit -- callers do, in the same transaction
as the change being audited, so an audit row is never written for a change
that didn't actually persist.

Cross-service actions (identity's user/role management) aren't covered:
AuditLog lives in city-core's own database, and identity has no access to
it (each service owns its own database -- see docs/architecture.md). Giving
identity a real audit trail would mean either its own AuditLog table or
publishing audit events over Kafka the way Phase 3's live data pipeline
does; that's a separate, larger piece of work, not something to fake here.
"""

from app.db.models import AuditLog


def record(
    db,
    *,
    actor: str,
    action: str,
    target_resource: str,
    department_code: str | None = None,
    reason: str | None = None,
    approved_by: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=action,
        target_resource=target_resource,
        department_code=department_code,
        reason=reason,
        approved_by=approved_by,
    )
    db.add(entry)
    return entry
