"""Outbound email for verification and password-reset links.

CityOS is software-only and intentionally does not ship an SMTP/SES
integration -- wiring one in is a deployment concern, not a platform one.
Every environment logs the dispatch via structlog; non-production
environments also append to an in-process outbox so tests (and local
development, via the log stream) can see exactly what would have been
sent without any network access or mail server.
"""

import structlog

from app.core.config import Settings

logger = structlog.get_logger()

# Populated outside production only. Tests read from this to assert on
# verification/reset links without a real mail transport.
OUTBOX: list[dict[str, str]] = []


def send_email(settings: Settings, *, to: str, subject: str, body: str) -> None:
    logger.info("email_dispatched", to=to, subject=subject)
    if settings.app_env != "production":
        OUTBOX.append({"to": to, "subject": subject, "body": body})


def send_verification_email(settings: Settings, *, to: str, token: str) -> None:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    send_email(
        settings, to=to, subject="Verify your CityOS account", body=f"Verify your email: {link}"
    )


def send_password_reset_email(settings: Settings, *, to: str, token: str) -> None:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    send_email(
        settings, to=to, subject="Reset your CityOS password", body=f"Reset your password: {link}"
    )
