"""Incident lifecycle rules (spec section 16).

    DETECTED -> VERIFIED -> ASSIGNED -> RESPONDING -> RESOLVED -> ANALYZED

Enforced here rather than left to callers, so an incident can never skip a
stage or move backwards through the API.
"""

import uuid

from app.core.errors import AppError

TRANSITIONS: dict[str, set[str]] = {
    "DETECTED": {"VERIFIED"},
    "VERIFIED": {"ASSIGNED"},
    "ASSIGNED": {"RESPONDING"},
    "RESPONDING": {"RESOLVED"},
    "RESOLVED": {"ANALYZED"},
    "ANALYZED": set(),
}


def generate_incident_number() -> str:
    return f"INC-{uuid.uuid4().hex[:8].upper()}"


def validate_transition(current: str, target: str) -> None:
    allowed = TRANSITIONS.get(current, set())
    if target not in allowed:
        raise AppError(
            409,
            "INVALID_STATUS_TRANSITION",
            f"Cannot move an incident from {current} to {target}. "
            f"Allowed next state(s): {sorted(allowed) or 'none (terminal)'}.",
        )


def require_status(current: str, expected: str, action: str) -> None:
    if current != expected:
        raise AppError(
            409,
            "INVALID_STATUS_TRANSITION",
            f"Cannot {action} an incident that is {current} (expected {expected}).",
        )
