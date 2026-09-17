import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, get_current_user, get_db
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.core.time import ensure_aware
from app.db.models import (
    EmailVerificationToken,
    OAuthAccount,
    PasswordResetToken,
    RefreshToken,
    Role,
    User,
)
from app.db.seed_data import DEFAULT_SELF_REGISTRATION_ROLE
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    RequestPasswordResetRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from app.schemas.common import MessageResponse
from app.services.email import send_password_reset_email, send_verification_email
from app.services.oauth import build_authorize_url, exchange_code, verify_state
from app.services.permissions import resolve_permissions
from app.services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_INACTIVE_STATUSES = ("SUSPENDED", "DEACTIVATED")


def _expiry(seconds: int) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=seconds)


async def _load_role(db: AsyncSession, code: str) -> Role:
    role = await db.scalar(
        select(Role).options(selectinload(Role.permissions)).where(Role.code == code)
    )
    if role is None:
        raise AppError(400, "ROLE_NOT_FOUND", f"Role '{code}' does not exist.")
    return role


async def _load_user_with_role(
    db: AsyncSession, *, email: str | None = None, user_id: uuid.UUID | None = None
) -> User | None:
    stmt = select(User).options(
        selectinload(User.role).selectinload(Role.permissions), selectinload(User.department)
    )
    if email is not None:
        stmt = stmt.where(User.email == email)
    elif user_id is not None:
        stmt = stmt.where(User.id == user_id)
    else:  # pragma: no cover - programmer error
        raise ValueError("email or user_id is required")
    return await db.scalar(stmt)


def _access_token_for(settings: Settings, user: User) -> str:
    return create_access_token(
        settings,
        user_id=user.id,
        email=user.email,
        role_code=user.role.code,
        department_code=user.department.code if user.department else None,
        permissions=resolve_permissions(user.role),
    )


async def _create_refresh_token(
    db: AsyncSession, settings: Settings, user_id: uuid.UUID
) -> tuple[str, RefreshToken]:
    raw, token_hash = generate_opaque_token()
    row = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=_expiry(settings.refresh_token_expire_days * 86400),
    )
    db.add(row)
    await db.flush()
    return raw, row


async def _issue_token_pair(db: AsyncSession, settings: Settings, user: User) -> TokenPair:
    access = _access_token_for(settings, user)
    raw_refresh, _ = await _create_refresh_token(db, settings, user.id)
    await db.commit()
    return TokenPair(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


def _reject_if_inactive(user: User) -> None:
    if user.status in _INACTIVE_STATUSES:
        raise AppError(403, "ACCOUNT_NOT_ACTIVE", f"This account is {user.status.lower()}.")


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RegisterResponse:
    email = payload.email.lower()
    if await db.scalar(select(User).where(User.email == email)):
        raise AppError(
            409, "EMAIL_ALREADY_REGISTERED", "An account with this email already exists."
        )
    role = await _load_role(db, DEFAULT_SELF_REGISTRATION_ROLE)
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role_id=role.id,
        status="PENDING_VERIFICATION",
    )
    db.add(user)
    await db.flush()
    raw_token, token_hash = generate_opaque_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=_expiry(settings.email_verification_token_expire_hours * 3600),
        )
    )
    await db.commit()
    send_verification_email(settings, to=user.email, token=raw_token)
    return RegisterResponse(id=str(user.id), email=user.email, status=user.status)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    email = payload.email.lower()
    client_ip = request.client.host if request.client else "unknown"
    allowed = await check_rate_limit(
        settings,
        key=f"login:{client_ip}:{email}",
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    if not allowed:
        raise AppError(429, "RATE_LIMITED", "Too many login attempts. Try again shortly.")

    user = await _load_user_with_role(db, email=email)
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise AppError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    _reject_if_inactive(user)

    user.last_login_at = datetime.now(UTC)
    return await _issue_token_pair(db, settings, user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    token_hash = hash_opaque_token(payload.refresh_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if (
        stored is None
        or stored.revoked_at is not None
        or ensure_aware(stored.expires_at) < datetime.now(UTC)
    ):
        raise AppError(401, "TOKEN_INVALID", "Refresh token is invalid, expired, or already used.")

    user = await _load_user_with_role(db, user_id=stored.user_id)
    if user is None:
        raise AppError(401, "TOKEN_INVALID", "Refresh token is invalid, expired, or already used.")
    _reject_if_inactive(user)

    stored.revoked_at = datetime.now(UTC)
    raw_refresh, new_row = await _create_refresh_token(db, settings, user.id)
    stored.replaced_by_id = new_row.id
    access = _access_token_for(settings, user)
    await db.commit()
    return TokenPair(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    token_hash = hash_opaque_token(payload.refresh_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        await db.commit()
    return MessageResponse(message="Logged out.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    token_hash = hash_opaque_token(payload.token)
    stored = await db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    if (
        stored is None
        or stored.used_at is not None
        or ensure_aware(stored.expires_at) < datetime.now(UTC)
    ):
        raise AppError(400, "TOKEN_INVALID", "Verification token is invalid or has expired.")
    user = await db.get(User, stored.user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "User no longer exists.")
    stored.used_at = datetime.now(UTC)
    user.email_verified_at = datetime.now(UTC)
    if user.status == "PENDING_VERIFICATION":
        user.status = "ACTIVE"
    await db.commit()
    return MessageResponse(message="Email verified.")


@router.post("/resend-verification", response_model=MessageResponse, status_code=202)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is not None and user.email_verified_at is None:
        raw_token, token_hash = generate_opaque_token()
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=_expiry(settings.email_verification_token_expire_hours * 3600),
            )
        )
        await db.commit()
        send_verification_email(settings, to=user.email, token=raw_token)
    return MessageResponse(
        message="If that account exists and is unverified, a new email has been sent."
    )


@router.post("/request-password-reset", response_model=MessageResponse, status_code=202)
async def request_password_reset(
    payload: RequestPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is not None:
        raw_token, token_hash = generate_opaque_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=_expiry(settings.password_reset_token_expire_minutes * 60),
            )
        )
        await db.commit()
        send_password_reset_email(settings, to=user.email, token=raw_token)
    return MessageResponse(message="If that account exists, a password reset email has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    token_hash = hash_opaque_token(payload.token)
    stored = await db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    if (
        stored is None
        or stored.used_at is not None
        or ensure_aware(stored.expires_at) < datetime.now(UTC)
    ):
        raise AppError(400, "TOKEN_INVALID", "Password reset token is invalid or has expired.")
    user = await db.get(User, stored.user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "User no longer exists.")

    user.hashed_password = hash_password(payload.new_password)
    stored.used_at = datetime.now(UTC)
    active_tokens = await db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
        )
    )
    for token in active_tokens:
        token.revoked_at = datetime.now(UTC)
    await db.commit()
    return MessageResponse(message="Password has been reset.")


@router.get("/me", response_model=MeResponse)
async def me(
    current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MeResponse:
    user = await _load_user_with_role(db, user_id=uuid.UUID(current.id))
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "User no longer exists.")
    return MeResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.code,
        department=user.department.code if user.department else None,
        permissions=resolve_permissions(user.role),
        email_verified=user.email_verified_at is not None,
        status=user.status,
    )


@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(
    provider: str, settings: Settings = Depends(get_settings)
) -> RedirectResponse:
    return RedirectResponse(build_authorize_url(settings, provider=provider))


@router.get("/oauth/{provider}/callback", response_model=TokenPair)
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    verify_state(settings, state=state, provider=provider)
    profile = await exchange_code(settings, provider=provider, code=code)

    account = await db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == profile.provider_account_id,
        )
    )
    if account is not None:
        user = await _load_user_with_role(db, user_id=account.user_id)
        if user is None:
            raise AppError(404, "USER_NOT_FOUND", "User no longer exists.")
    else:
        email = profile.email.lower()
        user = await db.scalar(select(User).where(User.email == email))
        if user is None:
            role = await _load_role(db, DEFAULT_SELF_REGISTRATION_ROLE)
            user = User(
                email=email,
                full_name=profile.full_name,
                role_id=role.id,
                status="ACTIVE",
                email_verified_at=datetime.now(UTC),
            )
            db.add(user)
            await db.flush()
        db.add(
            OAuthAccount(
                user_id=user.id, provider=provider, provider_account_id=profile.provider_account_id
            )
        )
        await db.flush()
        user = await _load_user_with_role(db, user_id=user.id)
        if user is None:  # pragma: no cover - defensive
            raise AppError(500, "INTERNAL_ERROR", "Failed to load the linked account.")

    _reject_if_inactive(user)
    user.last_login_at = datetime.now(UTC)
    return await _issue_token_pair(db, settings, user)
