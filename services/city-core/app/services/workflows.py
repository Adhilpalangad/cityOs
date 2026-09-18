"""Workflow task lifecycle rules (spec section 45: creation, assignment,
approval/rejection, escalation, SLA, status tracking).

Same shape as app/services/incidents.py: a plain transition map enforced
here so the API can never move a task through an invalid state, rather
than trusting callers to only send valid transitions.

    PENDING -> IN_PROGRESS -> COMPLETED
       |            |  ^
       v            v  |
    REJECTED    ESCALATED
"""

import uuid

from app.core.errors import AppError

TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"IN_PROGRESS", "REJECTED"},
    "IN_PROGRESS": {"COMPLETED", "ESCALATED", "REJECTED"},
    "ESCALATED": {"IN_PROGRESS", "REJECTED"},
    "COMPLETED": set(),
    "REJECTED": set(),
}


def generate_task_number() -> str:
    return f"TSK-{uuid.uuid4().hex[:8].upper()}"


def validate_transition(current: str, target: str) -> None:
    allowed = TRANSITIONS.get(current, set())
    if target not in allowed:
        raise AppError(
            409,
            "INVALID_STATUS_TRANSITION",
            f"Cannot move a workflow task from {current} to {target}. "
            f"Allowed next state(s): {sorted(allowed) or 'none (terminal)'}.",
        )
