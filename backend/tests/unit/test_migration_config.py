"""Konfiguration des Migrationspfads.

Eine Migration braucht die Datenbank und sonst nichts. Diese Tests halten
die Trennung fest, weil sie sich lautlos wieder schliesst: es genuegt, in
`alembic/env.py` einmal `get_settings()` zu schreiben, und `alembic
upgrade head` haengt wieder an SMTP- und Cursor-Key-Pruefungen.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sidebyside.config import DEFAULT_DATABASE_URL, DatabaseSettings, Settings


def test_migration_braucht_keine_production_runtimewerte(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Der Fall aus #110: Production ohne Cursor-Key, Mail und HTTPS-Adresse."""
    monkeypatch.setenv("SBS_ENVIRONMENT", "production")
    monkeypatch.setenv("SBS_DEPLOYMENT", "self_hosted")
    monkeypatch.setenv("SBS_DATABASE_URL", "postgresql+psycopg://u:p@postgres:5432/sidebyside")
    monkeypatch.delenv("SBS_CURSOR_SIGNING_KEY", raising=False)

    # Die Anwendung verweigert hier den Start - zu Recht.
    with pytest.raises(ValidationError, match="SBS_CURSOR_SIGNING_KEY"):
        Settings()

    # Die Migration nicht: sie liest nur die Verbindung.
    assert DatabaseSettings().database_url == "postgresql+psycopg://u:p@postgres:5432/sidebyside"


@pytest.mark.parametrize("leer", ["", "   "])
def test_leere_datenbank_url_ist_in_beiden_pfade_ein_fehler(
    monkeypatch: pytest.MonkeyPatch, leer: str
) -> None:
    """Runtime und Migration teilen dieselbe Regel fuer leere Interpolation."""
    monkeypatch.setenv("SBS_DATABASE_URL", leer)

    with pytest.raises(ValidationError, match="SBS_DATABASE_URL"):
        DatabaseSettings()
    with pytest.raises(ValidationError, match="SBS_DATABASE_URL"):
        Settings()


def test_vorgabewert_bleibt_mit_der_anwendung_gleich(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zwei Konfigurationen, eine Entwicklungsdatenbank.

    Liefen die Vorgabewerte auseinander, migrierte ein lokaler Lauf eine
    andere Datenbank als die, gegen die die Anwendung startet.
    """
    monkeypatch.delenv("SBS_DATABASE_URL", raising=False)

    assert DatabaseSettings().database_url == DEFAULT_DATABASE_URL
    assert Settings().database_url == DEFAULT_DATABASE_URL
