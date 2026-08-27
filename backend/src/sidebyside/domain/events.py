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
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from sidebyside.authorization import ContentVisibility


class EventType(StrEnum):
    """Der Katalog. Ein ausgelieferter Name wird nicht umbenannt."""

    MEMORY_CREATED = "MEMORY_CREATED"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    MEMORY_DELETED = "MEMORY_DELETED"
    HEART_MOMENT_CREATED = "HEART_MOMENT_CREATED"
    HEART_MOMENT_UPDATED = "HEART_MOMENT_UPDATED"
    HEART_MOMENT_DELETED = "HEART_MOMENT_DELETED"
    HEART_MOMENT_VISIBILITY_CHANGED = "HEART_MOMENT_VISIBILITY_CHANGED"
    MILESTONE_CREATED = "MILESTONE_CREATED"
    MILESTONE_UPDATED = "MILESTONE_UPDATED"
    MILESTONE_DELETED = "MILESTONE_DELETED"
    COMMENT_CREATED = "COMMENT_CREATED"
    WISH_CREATED = "WISH_CREATED"
    WISH_UPDATED = "WISH_UPDATED"
    WISH_DELETED = "WISH_DELETED"
    # Die drei Wish-Statuskanten aus M3-D02/D03/D04. Eigene Typen statt
    # `WISH_UPDATED`: fuer einen Consumer ist "eingeplant" eine andere
    # Nachricht als "umbenannt".
    WISH_PLANNED = "WISH_PLANNED"
    WISH_REOPENED = "WISH_REOPENED"
    PLACE_CREATED = "PLACE_CREATED"
    PLACE_UPDATED = "PLACE_UPDATED"
    PLACE_DELETED = "PLACE_DELETED"
    # Die typisierten Content-Relations aus M3-D08. Eigene Typen statt
    # `PLACE_UPDATED`: eine Verknuepfung aendert den Ort nicht, sie stellt
    # eine Beziehung her - und ein Consumer, der Orte spiegelt, muss davon
    # nichts neu laden.
    PLACE_MEMORY_LINKED = "PLACE_MEMORY_LINKED"
    PLACE_MEMORY_UNLINKED = "PLACE_MEMORY_UNLINKED"
    PLACE_HEART_MOMENT_LINKED = "PLACE_HEART_MOMENT_LINKED"
    PLACE_HEART_MOMENT_UNLINKED = "PLACE_HEART_MOMENT_UNLINKED"
    PLACE_MILESTONE_LINKED = "PLACE_MILESTONE_LINKED"
    PLACE_MILESTONE_UNLINKED = "PLACE_MILESTONE_UNLINKED"
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_UPDATED = "PLAN_UPDATED"
    PLAN_DELETED = "PLAN_DELETED"
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
    visibility: ContentVisibility | None = None

    target_type: Literal["MEMORY", "HEART_MOMENT", "MILESTONE"] | None = None
    target_id: UUID | None = None
    recipient_id: UUID | None = None
    """Sichere Comment-Referenzen fuer einen spaeteren Notification-Consumer.

    Ausschliesslich IDs und die geschlossene Target-Kategorie. Comment-Body,
    Parent-Titel/-Text und HeartMoment-Emotion duerfen hier nicht auftauchen.
    """


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
