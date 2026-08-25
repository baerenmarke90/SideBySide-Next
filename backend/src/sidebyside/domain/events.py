"""Domain-Ereignisse.

Die Domäne kennt weder Push noch Mail noch eine Integration. Sie stellt
fest, dass etwas geschehen ist; was daraus folgt, entscheidet ein Worker.

Ereignisnutzlasten enthalten bewusst KEINE sensiblen Inhalte. Ein Ereignis
transportiert Verweise - wer, wo, welches Objekt -, nicht den Text einer
Erinnerung. Zwei Gründe: die Nutzlast überlebt in der Outbox und in Logs,
und nach der Umstellung auf Ende-zu-Ende-Verschlüsselung stünde der Text
ohnehin nicht mehr zur Verfügung.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    """Der Katalog. Ein ausgelieferter Name wird nicht umbenannt."""

    MEMORY_CREATED = "MEMORY_CREATED"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    MEMORY_DELETED = "MEMORY_DELETED"
    HEART_MOMENT_CREATED = "HEART_MOMENT_CREATED"
    MILESTONE_CREATED = "MILESTONE_CREATED"
    COMMENT_CREATED = "COMMENT_CREATED"
    PLAN_COMPLETED = "PLAN_COMPLETED"
    WISH_COMPLETED = "WISH_COMPLETED"
    IMPORTANT_DATE_APPROACHING = "IMPORTANT_DATE_APPROACHING"
    PARTNER_THINKING_OF_YOU = "PARTNER_THINKING_OF_YOU"
    REMINDER_DUE = "REMINDER_DUE"
    PROFILE_PREFERENCE_CHANGED = "PROFILE_PREFERENCE_CHANGED"
    PARTNER_JOINED = "PARTNER_JOINED"


class PublicEventPayload(BaseModel):
    """Explizite Allowlist für dauerhaft gespeicherte Ereignismetadaten.

    „Public“ bedeutet hier nur: außerhalb eines ProtectedPayload sicher
    transportierbar. Es ist keine öffentliche API und keine Freigabe an
    Dritte. Neue Felder brauchen eine bewusste Prüfung an dieser zentralen
    Grenze; beliebige Dictionaries und damit Klartexte sind ausgeschlossen.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    has_attachment: bool | None = None


class DomainEvent(BaseModel):
    """Ein fachliches Ereignis.

    `payload` ist auf Verweise und unkritische Merkmale beschränkt. Wer
    Inhalt braucht, lädt ihn beim Verarbeiten aus der Domäne - dann greifen
    die Sichtbarkeitsregeln erneut, statt dass eine Kopie an ihnen vorbei
    unterwegs ist.

    Fuer M2 bildet die Outbox-Zeile zusammen mit diesem Objekt den in #68
    festgelegten Minimal-Envelope: Outbox-ID = eventId, createdAt = occurredAt,
    subject_type/-id = resourceType/-Id und `resource_version` = resourceVersion.
    Aeltere Nicht-M2-Events duerfen die Version weiterhin weglassen.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: EventType
    space_id: UUID
    actor_id: UUID | None = None
    subject_type: str
    subject_id: UUID
    resource_version: int | None = Field(default=None, ge=1)
    payload: PublicEventPayload = Field(default_factory=PublicEventPayload)
