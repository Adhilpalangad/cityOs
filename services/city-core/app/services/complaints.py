"""Citizen complaint lifecycle rules (spec section 44):

    Citizen -> Create Complaint -> ... -> Department Assignment ->
    Officer -> Resolution -> Citizen Notification

Same shape as app/services/incidents.py and app/services/workflows.py: a
plain transition map enforced here, not left to callers.

    SUBMITTED -> IN_REVIEW -> ASSIGNED -> RESOLVED
         \\            \\
          -> REJECTED   -> REJECTED
"""

import uuid

from app.core.errors import AppError

TRANSITIONS: dict[str, set[str]] = {
    "SUBMITTED": {"IN_REVIEW", "REJECTED"},
    "IN_REVIEW": {"ASSIGNED", "REJECTED"},
    "ASSIGNED": {"RESOLVED"},
    "RESOLVED": set(),
    "REJECTED": set(),
}


def generate_complaint_number() -> str:
    return f"CMP-{uuid.uuid4().hex[:8].upper()}"


def validate_transition(current: str, target: str) -> None:
    allowed = TRANSITIONS.get(current, set())
    if target not in allowed:
        raise AppError(
            409,
            "INVALID_STATUS_TRANSITION",
            f"Cannot move a complaint from {current} to {target}. "
            f"Allowed next state(s): {sorted(allowed) or 'none (terminal)'}.",
        )
