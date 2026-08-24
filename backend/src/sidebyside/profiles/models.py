"""Persistenz fuer Partnerprofile und Praeferenzen.

`PartnerProfile` ist das sichtbare SELF_PROFILE eines Accounts in genau
einem Space. Private Notizen ueber den Partner werden bewusst nicht an
dieses sichtbare Profil gehaengt: sie sind `ProfilePreference`-Zeilen mit
`PRIVATE_PARTNER_NOTE` und damit `OWNER_ONLY`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from pydantic import Field
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from sidebyside.authorization import (
    PrivacyClass,
    PrivateResourceMixin,
    ResourceAbsence,
)
from sidebyside.db.base import Base
from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin
from sidebyside.db.protected_payload import ProtectedPayloadJSON
from sidebyside.domain.payload import CRYPTO_VERSION_PLAINTEXT, ProtectedPayload


class ProfileVisibility(StrEnum):
    SELF_PROFILE = "SELF_PROFILE"
    PRIVATE_PARTNER_NOTE = "PRIVATE_PARTNER_NOTE"


class PreferenceCategory(StrEnum):
    FOOD = "FOOD"
    DRINK = "DRINK"
    FLOWERS = "FLOWERS"
    MOVIES = "MOVIES"
    SERIES = "SERIES"
    MUSIC = "MUSIC"
    HOBBIES = "HOBBIES"
    ACTIVITIES = "ACTIVITIES"
    TRAVEL = "TRAVEL"
    RESTAURANTS = "RESTAURANTS"
    COLORS = "COLORS"
    OTHER = "OTHER"


class PreferenceSentiment(StrEnum):
    LOVE = "LOVE"
    LIKE = "LIKE"
    NEUTRAL = "NEUTRAL"
    DISLIKE = "DISLIKE"
    AVOID = "AVOID"


class ProfilePreferencePayload(ProtectedPayload):
    """Der schuetenswerte Klartext einer Praeferenz.

    Version 1 speichert ihn als JSONB-Klartext. Die getrennte Payload-Grenze
    erlaubt spaeter Client-Verschluesselung, ohne Kategorie, Ownership und
    Privacy-Metadaten neu modellieren zu muessen.
    """

    value: str = Field(min_length=1, max_length=2000)


class PartnerProfile(IdMixin, TimestampMixin, PrivateResourceMixin, Base):
    """Das fuer den Partner sichtbare SELF_PROFILE eines Accounts."""

    __tablename__ = "partner_profiles"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Partner profile not found.", "PARTNER_PROFILE_NOT_FOUND"
    )

    __table_args__ = (
        UniqueConstraint("space_id", "owner_id", name="uq_partner_profiles_space_id_owner_id"),
        CheckConstraint("privacy_class = 'SPACE_SHARED'", name="privacy_is_space_shared"),
    )


class ProfilePreference(
    IdMixin,
    TimestampMixin,
    VersionMixin,
    PrivateResourceMixin,
    Base,
):
    """Eine strukturierte Praeferenz ueber sich selbst oder den Partner.

    `owner_id` ist der Autor/Eigentuemer, `account_id` die beschriebene
    Person. Die Kombination mit `visibility` ist in der Datenbank
    festgeschrieben:

    - SELF_PROFILE: Autor beschreibt sich selbst, SPACE_SHARED, Profil-FK.
    - PRIVATE_PARTNER_NOTE: Autor beschreibt den anderen, OWNER_ONLY, keine
      Verbindung zum sichtbaren PartnerProfile.
    """

    __tablename__ = "profile_preferences"

    privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
        "Profile preference not found.", "PROFILE_PREFERENCE_NOT_FOUND"
    )

    profile_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("partner_profiles.id", ondelete="CASCADE"),
    )
    account_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(16), nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    crypto_version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=CRYPTO_VERSION_PLAINTEXT,
        server_default=text("0"),
    )
    payload: Mapped[ProfilePreferencePayload] = mapped_column(
        ProtectedPayloadJSON(ProfilePreferencePayload),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "category IN ('FOOD', 'DRINK', 'FLOWERS', 'MOVIES', 'SERIES', 'MUSIC', "
            "'HOBBIES', 'ACTIVITIES', 'TRAVEL', 'RESTAURANTS', 'COLORS', 'OTHER')",
            name="category_is_known",
        ),
        CheckConstraint(
            "sentiment IN ('LOVE', 'LIKE', 'NEUTRAL', 'DISLIKE', 'AVOID')",
            name="sentiment_is_known",
        ),
        CheckConstraint(
            "visibility IN ('SELF_PROFILE', 'PRIVATE_PARTNER_NOTE')",
            name="visibility_is_known",
        ),
        CheckConstraint("crypto_version >= 0", name="crypto_version_is_non_negative"),
        CheckConstraint(
            "(visibility = 'SELF_PROFILE' AND account_id = owner_id "
            "AND privacy_class = 'SPACE_SHARED' AND profile_id IS NOT NULL) OR "
            "(visibility = 'PRIVATE_PARTNER_NOTE' AND account_id <> owner_id "
            "AND privacy_class = 'OWNER_ONLY' AND profile_id IS NULL)",
            name="visibility_matches_owner_and_privacy",
        ),
        Index(
            "ix_profile_preferences_space_id_account_id_visibility",
            "space_id",
            "account_id",
            "visibility",
        ),
        Index("ix_profile_preferences_owner_id", "owner_id"),
    )


def privacy_for(visibility: ProfileVisibility) -> PrivacyClass:
    """Privacy wird serverseitig aus der fachlichen Sichtbarkeit abgeleitet."""
    if visibility is ProfileVisibility.SELF_PROFILE:
        return PrivacyClass.SPACE_SHARED
    return PrivacyClass.OWNER_ONLY
