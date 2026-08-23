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
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
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
    # Klein geschrieben abgelegt. Sonst waeren "A@b.de" und "a@b.de" zwei
    # Adressen, und die Eindeutigkeit haette ein Loch.
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_primary: Mapped[bool] = mapped_column(nullable=False, default=False)

    account: Mapped[Account] = relationship(back_populates="emails")

    __table_args__ = (
        UniqueConstraint("email", name="uq_account_emails_email"),
        CheckConstraint("email = lower(email)", name="email_is_lowercase"),
    )


class AuthIdentity(IdMixin, TimestampMixin, Base):
    """Ein Anmeldeweg.

    `subject` ist der Bezeichner beim jeweiligen Verfahren: die Adresse beim
    Magic Link, die Credential-ID beim Passkey, das Subject beim OIDC.
    `secret_hash` traegt ausschliesslich Abgeleitetes - nie ein Geheimnis im
    Klartext.
    """

    __tablename__ = "auth_identities"

    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    secret_hash: Mapped[str | None] = mapped_column(String(255))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_auth_identities_provider_subject"),
        CheckConstraint(
            "provider IN ('MAGIC_LINK', 'PASSKEY', 'LOCAL_PASSWORD', 'OIDC')",
            name="provider_is_known",
        ),
        Index("ix_auth_identities_account_id", "account_id"),
    )


class DeviceSession(IdMixin, Base):
    """Eine angemeldete Geraetesitzung.

    Tokens werden ausschliesslich gehasht abgelegt. Wer die Datenbank liest,
    kann sich damit nicht anmelden - ein gestohlener Datenbestand ist
    schlimm genug, ohne dass er auch noch Zugang verschafft.

    `previous_refresh_token_hash` dient der Replay-Erkennung: taucht ein
    bereits rotierter Refresh Token wieder auf, ist er kopiert worden. Die
    Sitzung wird dann sofort widerrufen.
    """

    __tablename__ = "device_sessions"

    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    device_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    platform: Mapped[str] = mapped_column(String(32), nullable=False, default="")

    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_refresh_token_hash: Mapped[str | None] = mapped_column(String(64))

    access_token_hash: Mapped[str | None] = mapped_column(String(64))
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("refresh_token_hash", name="uq_device_sessions_refresh_token_hash"),
        Index("ix_device_sessions_access_token_hash", "access_token_hash"),
        Index("ix_device_sessions_account_id", "account_id"),
    )
