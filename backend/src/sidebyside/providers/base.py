"""Schnittstellen für externe Anbieter.

Der Domain-Code kennt keinen konkreten Anbieter. Externe Daten werden vor
dem Eintritt in die Domäne normalisiert - sonst tragen SideBySide-Objekte
über kurz oder lang die Eigenheiten fremder APIs mit sich herum, und ein
Anbieterwechsel wird zum Umbau.

Keine dieser Schnittstellen wird in M0 implementiert. Sie stehen hier,
damit spätere Integrationen einen vorgegebenen Platz haben.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum


@dataclass(frozen=True)
class GeoPoint:
    latitude: Decimal
    longitude: Decimal


@dataclass(frozen=True)
class PlaceCandidate:
    """Ein Ortsvorschlag aus einer externen Quelle."""

    external_id: str
    name: str
    address: str | None
    position: GeoPoint | None
    source: str


@dataclass(frozen=True)
class DiscoveryItem:
    """Eine normalisierte externe Veranstaltung oder Freizeitidee."""

    external_id: str
    title: str
    category: str
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    position: GeoPoint | None = None
    location_name: str | None = None
    source: str = ""
    source_url: str | None = None
    image_url: str | None = None


@dataclass(frozen=True)
class ExternalMediaItem:
    """Ein Foto oder Video in einem externen Dienst.

    Bewusst ein Verweis und keine Kopie. Ob später referenziert oder
    importiert wird, ist eine ausdrückliche Entscheidung.
    """

    external_id: str
    captured_at: datetime | None
    position: GeoPoint | None
    thumbnail_url: str | None
    source: str


class SharingMode(StrEnum):
    """Eine externe Verbindung ist nicht automatisch mit dem Partner geteilt."""

    PRIVATE = "PRIVATE"
    SPACE_SHARED = "SPACE_SHARED"


class GeocodingProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[PlaceCandidate]: ...

    @abstractmethod
    def reverse(self, position: GeoPoint) -> PlaceCandidate | None: ...


class DiscoveryProvider(ABC):
    @abstractmethod
    def find(
        self, position: GeoPoint, radius_km: int, on: date | None = None
    ) -> list[DiscoveryItem]: ...


class ExternalMediaProvider(ABC):
    @abstractmethod
    def find_by_date(self, on: date) -> list[ExternalMediaItem]: ...

    @abstractmethod
    def find_near(self, position: GeoPoint, radius_km: int) -> list[ExternalMediaItem]: ...


class LocationHistoryProvider(ABC):
    @abstractmethod
    def places_visited(self, on: date) -> list[PlaceCandidate]: ...
