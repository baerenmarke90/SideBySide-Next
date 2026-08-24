"""Provider bleiben abstrakt, normalisiert und frei konfigurierbar."""

from __future__ import annotations

import inspect
from decimal import Decimal

import pytest

from sidebyside.providers.base import (
    DiscoveryProvider,
    EntertainmentProvider,
    ExternalMediaProvider,
    GeocodingProvider,
    GeoPoint,
    LocationHistoryProvider,
    MapProvider,
    MapRoute,
    PlacesProvider,
    RecipeProvider,
)
from sidebyside.providers.registry import ProviderRegistry


class StraightLineMap(MapProvider):
    def route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        via: tuple[GeoPoint, ...] = (),
    ) -> MapRoute:
        return MapRoute(
            geometry=(origin, *via, destination),
            distance_meters=1,
            duration_seconds=1,
        )


def test_alle_geforderten_provider_sind_abstrakte_vertraege() -> None:
    interfaces = (
        MapProvider,
        GeocodingProvider,
        PlacesProvider,
        DiscoveryProvider,
        RecipeProvider,
        EntertainmentProvider,
        ExternalMediaProvider,
        LocationHistoryProvider,
    )
    assert all(inspect.isabstract(interface) for interface in interfaces)


def test_registry_waehlt_adapter_nur_ueber_konfigurierten_namen() -> None:
    registry = ProviderRegistry()
    adapter = StraightLineMap()
    registry.register(MapProvider, "self-hosted", adapter)

    assert registry.select(MapProvider, " SELF-HOSTED ") is adapter


def test_registry_weist_falschen_adaptertyp_ab() -> None:
    registry = ProviderRegistry()
    with pytest.raises(TypeError, match="MapProvider"):
        registry.register(MapProvider, "falsch", object())  # type: ignore[arg-type]


def test_map_vertrag_gibt_normalisiertes_internes_modell_zurueck() -> None:
    start = GeoPoint(Decimal("52.52"), Decimal("13.405"))
    ziel = GeoPoint(Decimal("52.51"), Decimal("13.39"))
    route = StraightLineMap().route(start, ziel)

    assert isinstance(route, MapRoute)
    assert route.geometry == (start, ziel)
    assert type(route).__module__ == "sidebyside.providers.base"
