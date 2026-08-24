"""Konfigurierbare Auswahl von Provider-Adaptern an der Composition Root."""

from __future__ import annotations

from typing import TypeVar, cast

ProviderT = TypeVar("ProviderT")


class ProviderNotConfiguredError(LookupError):
    """Für Interface und konfigurierten Namen ist kein Adapter registriert."""


class ProviderRegistry:
    """Ordnet frei konfigurierbare Namen abstrakten Provider-Typen zu.

    Die Domain kennt nur das Interface. Ob eine Installation etwa einen
    lokalen, freien oder kommerziellen Adapter unter einem Namen registriert,
    entscheidet ausschließlich die Composition Root.
    """

    def __init__(self) -> None:
        self._providers: dict[tuple[type[object], str], object] = {}

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized = name.strip().casefold()
        if not normalized:
            raise ValueError("Provider-Name darf nicht leer sein")
        return normalized

    def register(self, interface: type[ProviderT], name: str, provider: ProviderT) -> None:
        if not isinstance(provider, interface):
            raise TypeError(f"Adapter implementiert {interface.__name__} nicht")
        key = (cast(type[object], interface), self._normalize_name(name))
        if key in self._providers:
            raise ValueError(f"Provider bereits registriert: {interface.__name__}/{name}")
        self._providers[key] = provider

    def select(self, interface: type[ProviderT], configured_name: str) -> ProviderT:
        key = (cast(type[object], interface), self._normalize_name(configured_name))
        provider = self._providers.get(key)
        if provider is None:
            raise ProviderNotConfiguredError(
                f"Kein Provider fuer {interface.__name__}/{configured_name} konfiguriert"
            )
        return cast(ProviderT, provider)
