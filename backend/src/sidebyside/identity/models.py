"""Identitaet.

Der Account traegt Profilidentitaet. Anmeldegeheimnisse liegen getrennt in
AuthIdentity - ein Account kann mehrere Wege haben, sich auszuweisen, und
keiner davon gehoert in die Tabelle, die eine Oberflaeche anzeigt.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin


class AuthProvider(StrEnum):
    """Wie sich ein Account ausweist.

    Cloud setzt auf Magic Link und Passkey ohne Passwortpflicht.
    Self-Hosted erlaubt zusaetzlich lokales Passwort und OIDC - damit ist
    ein externer Provider spaeter kein Sonderweg.
    """

    MAGIC_LINK = "MAGIC_LINK"
    PASSKEY = "PASSKEY"
    LOCAL_PASSWORD = "LOCAL_PASSWORD"
    OIDC = "OIDC"


class InstanceBootstrapState(Base):
    """Dauerhafter Einmaligkeitsnachweis fuer die Erstregistrierung.

    Der geheime Bootstrap-Wert steht ausschliesslich in der Laufzeit-
    Konfiguration. Die Datenbank merkt nur, ob die Inbetriebnahme bereits
    abgeschlossen ist.
    """

    __tablename__ = "instance_bootstrap_state"

    singleton_key: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
    )

    __table_args__ = (CheckConstraint("singleton_key = 1", name="singleton_key_is_one"),)


class Account(IdMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    birthday: Mapped[date | None] = mapped_column(Date)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="de-DE")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Berlin")
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    emails: Mapped[list[AccountEmail]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    @property
    def is_active(self) -> bool:
        return self.disabled_at is None


class AccountEmail(IdMixin, TimestampMixin, Base):
    """Eine E-Mail-Adresse eines Accounts.

    Getrennt vom Account, weil eine Adresse wechseln kann und weil
    Verifikation ein Zustand der Adresse ist, nicht der Person.
    """

    __tablename__ = "account_emails"

    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_primary: Mapped[bool] = mapped_column(nullable=False, default=False)

    account: Mapped[Account] = relationship(back_populates="emails")

    __table_args__ = (
        UniqueConstraint("email", name="uq_account_emails_email"),
        CheckConstraint("email = lower(email)", name="email_is_lowercase"),
    )


class AuthIdentity(IdMixin, TimestampMixin, Base):
    """Ein Anmeldeweg."""

    __tablename__ = "auth_identities"

    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(512))
    connection_id: Mapped[str | None] = mapped_column(String(128))
    secret_hash: Mapped[str | None] = mapped_column(String(255))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("issuer", "subject", name="uq_auth_identities_issuer_subject"),
        CheckConstraint(
            "provider IN ('MAGIC_LINK', 'PASSKEY', 'LOCAL_PASSWORD', 'OIDC')",
            name="provider_is_known",
        ),
        CheckConstraint(
            "(provider = 'OIDC' AND issuer IS NOT NULL AND connection_id IS NOT NULL) "
            "OR (provider <> 'OIDC' AND issuer IS NULL AND connection_id IS NULL)",
            name="oidc_metadata_matches_provider",
        ),
        Index(
            "uq_auth_identities_non_oidc_provider_subject",
            "provider",
            "subject",
            unique=True,
            postgresql_where=text("provider <> 'OIDC'"),
        ),
        Index("ix_auth_identities_account_id", "account_id"),
    )


class WebAuthnCredential(IdMixin, TimestampMixin, Base):
    __tablename__ = "webauthn_credentials"

    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    aaguid: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    transports: Mapped[list[str]] = mapped_column(
        postgresql.JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    is_discoverable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    backup_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    backup_state: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("credential_id", name="uq_webauthn_credentials_credential_id"),
        CheckConstraint("sign_count >= 0", name="sign_count_is_non_negative"),
        Index("ix_webauthn_credentials_account_id", "account_id"),
    )


class WebAuthnChallenge(IdMixin, Base):
    __tablename__ = "webauthn_challenges"

    purpose: Mapped[str] = mapped_column(String(16), nullable=False)
    challenge: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    account_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("purpose IN ('REGISTRATION', 'AUTHENTICATION')", name="purpose_is_known"),
        Index("ix_webauthn_challenges_expires_at", "expires_at"),
    )


class OneTimeTokenMixin:
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def is_open(self, at: datetime) -> bool:
        return self.consumed_at is None and self.revoked_at is None and self.expires_at > at


class EmailVerificationToken(IdMixin, OneTimeTokenMixin, Base):
    __tablename__ = "email_verification_tokens"
    account_email_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("account_emails.id", ondelete="CASCADE"), nullable=False
    )
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_email_verification_tokens_token_hash"),
        Index("ix_email_verification_tokens_account_email_id", "account_email_id"),
        Index("ix_email_verification_tokens_expires_at", "expires_at"),
    )


class MagicLinkToken(IdMixin, OneTimeTokenMixin, Base):
    __tablename__ = "magic_link_tokens"
    account_email_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("account_emails.id", ondelete="CASCADE"), nullable=False
    )
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_magic_link_tokens_token_hash"),
        Index("ix_magic_link_tokens_account_email_id", "account_email_id"),
        Index("ix_magic_link_tokens_expires_at", "expires_at"),
    )


class AccountRecoveryToken(IdMixin, OneTimeTokenMixin, Base):
    __tablename__ = "account_recovery_tokens"
    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_account_recovery_tokens_token_hash"),
        Index("ix_account_recovery_tokens_account_id", "account_id"),
        Index("ix_account_recovery_tokens_expires_at", "expires_at"),
    )


class OidcAuthRequest(IdMixin, Base):
    """Eine begonnene OIDC-Anmeldung.

    Der optionale ``invitation_token_hash`` bindet ein Invite-Onboarding an
    genau diesen State, ohne den Bearer-Token im Klartext zu speichern oder
    an den externen Anbieter zu senden.
    """

    __tablename__ = "oidc_auth_requests"

    connection_id: Mapped[str] = mapped_column(String(64), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False)
    code_verifier: Mapped[str] = mapped_column(String(128), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    account_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE")
    )
    invitation_token_hash: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("state_hash", name="uq_oidc_auth_requests_state_hash"),
        Index("ix_oidc_auth_requests_expires_at", "expires_at"),
    )


class DeviceSession(IdMixin, Base):
    __tablename__ = "device_sessions"

    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    platform: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    access_token_hash: Mapped[str | None] = mapped_column(String(64))
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("refresh_token_hash", name="uq_device_sessions_refresh_token_hash"),
        Index("ix_device_sessions_access_token_hash", "access_token_hash"),
        Index("ix_device_sessions_account_id", "account_id"),
    )


class ConsumedRefreshToken(IdMixin, Base):
    __tablename__ = "consumed_refresh_tokens"

    device_session_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("device_sessions.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_consumed_refresh_tokens_token_hash"),
        Index("ix_consumed_refresh_tokens_device_session_id", "device_session_id"),
    )


class RateLimitEvent(IdMixin, Base):
    __tablename__ = "rate_limit_events"

    action: Mapped[str] = mapped_column(String(32), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    __table_args__ = (
        Index(
            "ix_rate_limit_events_action_key_hash_occurred_at",
            "action",
            "key_hash",
            "occurred_at",
        ),
    )
