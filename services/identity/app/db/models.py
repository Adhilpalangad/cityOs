import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# --- Status / provider value sets (kept as plain strings, validated by
# Pydantic at the API boundary, so SQLite and PostgreSQL share one schema). ---
USER_STATUSES = ("PENDING_VERIFICATION", "ACTIVE", "SUSPENDED", "DEACTIVATED")
OAUTH_PROVIDERS = ("google", "github")


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(sa.Uuid(), primary_key=True, default=uuid.uuid4)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(sa.String(255), nullable=False)


role_permissions = sa.Table(
    "role_permissions",
    Base.metadata,
    sa.Column(
        "role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    sa.Column(
        "permission_id",
        sa.Uuid(),
        sa.ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    is_platform_role: Mapped[bool] = mapped_column(sa.Boolean(), default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    department: Mapped[Department | None] = relationship()
    permissions: Mapped[list[Permission]] = relationship(secondary=role_permissions)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(), sa.ForeignKey("roles.id"), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        sa.String(30), nullable=False, default="PENDING_VERIFICATION"
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    role: Mapped[Role] = relationship()
    department: Mapped[Department | None] = relationship()

    __table_args__ = (sa.CheckConstraint(f"status IN {USER_STATUSES}", name="ck_users_status"),)


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    __table_args__ = (
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_oauth_provider_account"),
        sa.CheckConstraint(f"provider IN {OAUTH_PROVIDERS}", name="ck_oauth_provider"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
