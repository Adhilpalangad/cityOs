"""Notification Engine (spec section 48): a real notify() writer plus the
trigger rules spec section 48 gives as its own worked examples --

    IF incident severity = CRITICAL -> notify Emergency Control
    IF hospital capacity exceeds a threshold -> notify Health Control

wired into app/api/routes_incidents.py, app/api/routes_roads.py, and
app/api/routes_hospitals.py. "Road closure affects a citizen zone" (spec's
third example) needs a zone/citizen model this codebase doesn't have yet,
so the road rule here is the narrower, honest version: any road closure
notifies its own department.

Like app/services/audit.py, this module doesn't own the DB session --
callers commit, in the same transaction as the change that triggered it.
"""

from app.db.models import Notification

# ICU occupancy at or above this fraction triggers a capacity notification
# (spec section 17's own worked example uses 42/50 ICU beds -- 84% -- as a
# HIGH emergency-capacity case; 90% is used elsewhere in this codebase's
# demo data as the "critical" threshold, so that's what's enforced here).
ICU_CAPACITY_ALERT_THRESHOLD = 0.9


def notify(
    db,
    *,
    title: str,
    message: str,
    severity: str = "INFO",
    target_department: str | None = None,
    channel: str = "IN_APP",
) -> Notification:
    entry = Notification(
        title=title,
        message=message,
        severity=severity,
        target_department=target_department,
        channel=channel,
    )
    db.add(entry)
    return entry
