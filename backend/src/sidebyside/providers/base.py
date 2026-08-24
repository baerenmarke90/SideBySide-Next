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
class MapRoute:
    """Eine anbieterneutrale Route; Geometrie und Kennzahlen sind SI-Werte."""

    geometry: tuple[GeoPoint, ...]
    distance_meters: int
    duration_seconds: int


@dataclass(frozen=True)
class RecipeIngredient:
    name: str
    amount: Decimal | None = None
    unit: str | None = None


@dataclass(frozen=True)
class RecipeItem:
    """Normalisierte Rezeptdaten ohne DTO eines konkreten Katalogs."""

    external_id: str
    title: str
    ingredients: tuple[RecipeIngredient, ...]
    instructions: tuple[str, ...]
    source: str
    description: str | None = None
    total_minutes: int | None = None
    source_url: str | None = None
    image_url: str | None = None


class EntertainmentKind(StrEnum):
    MOVIE = "MOVIE"
    SERIES = "SERIES"
    BOOK = "BOOK"
    GAME = "GAME"
    MUSIC = "MUSIC"
    OTHER = "OTHER"


@dataclass(frozen=True)
class EntertainmentItem:
    """Normalisierter Medienfund, unabhängig von Shop oder Streamingdienst."""

    external_id: str
    title: str
    kind: EntertainmentKind
    source: str
    release_year: int | None = None
    description: str | None = None
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


class MapProvider(ABC):
    @abstractmethod
    def route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        via: tuple[GeoPoint, ...] = (),
    ) -> MapRoute: ...


class GeocodingProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[PlaceCandidate]: ...

    @abstractmethod
    def reverse(self, position: GeoPoint) -> PlaceCandidate | None: ...


class PlacesProvider(ABC):
    @abstractmethod
    def search(
        self,
        query: str,
        near: GeoPoint | None = None,
        radius_km: int | None = None,
        limit: int = 10,
    ) -> list[PlaceCandidate]: ...

    @abstractmethod
    def get(self, external_id: str) -> PlaceCandidate | None: ...


class DiscoveryProvider(ABC):
    @abstractmethod
    def find(
        self, position: GeoPoint, radius_km: int, on: date | None = None
    ) -> list[DiscoveryItem]: ...


class RecipeProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[RecipeItem]: ...

    @abstractmethod
    def get(self, external_id: str) -> RecipeItem | None: ...


class EntertainmentProvider(ABC):
    @abstractmethod
    def search(
        self,
        query: str,
        kinds: tuple[EntertainmentKind, ...] = (),
        limit: int = 20,
    ) -> list[EntertainmentItem]: ...


class ExternalMediaProvider(ABC):
    @abstractmethod
    def find_by_date(self, on: date) -> list[ExternalMediaItem]: ...

    @abstractmethod
    def find_near(self, position: GeoPoint, radius_km: int) -> list[ExternalMediaItem]: ...


class LocationHistoryProvider(ABC):
    @abstractmethod
    def places_visited(self, on: date) -> list[PlaceCandidate]: ...
