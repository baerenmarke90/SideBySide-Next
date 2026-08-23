"""Ablage im Dateisystem.

Der Schwerpunkt liegt auf dem Pfad: ein Storage Key, der aus dem
Wurzelverzeichnis herausfuehrt, waere ein Schreib- oder Lesezugriff auf
beliebige Dateien des Servers.
"""

from __future__ import annotations

import io
from datetime import timedelta
from pathlib import Path
from uuid import UUID

import pytest

from sidebyside.core.ids import new_id
from sidebyside.media.base import build_storage_key
from sidebyside.media.local import LocalMediaStore


@pytest.fixture
def store(tmp_path: Path) -> LocalMediaStore:
    return LocalMediaStore(tmp_path / "media")


class TestStorageKey:
    def test_besteht_nur_aus_uuids(self) -> None:
        space, anhang = new_id(), new_id()
        assert build_storage_key(space, anhang) == (f"spaces/{space}/attachments/{anhang}/original")

    def test_enthaelt_keinen_benutzer_dateinamen(self) -> None:
        """Ein Dateiname aus einer Anfrage kann Pfadbestandteile tragen."""
        schluessel = build_storage_key(new_id(), new_id())
        assert ".." not in schluessel
        assert schluessel.count("/") == 4

    def test_weist_eine_ausbrechende_variante_ab(self) -> None:
        for boese in ["../../etc/passwd", "a/b", ".."]:
            with pytest.raises(ValueError):
                build_storage_key(new_id(), new_id(), boese)


class TestAblage:
    def test_schreiben_lesen_loeschen(self, store: LocalMediaStore) -> None:
        schluessel = build_storage_key(new_id(), new_id())
        abgelegt = store.put(schluessel, io.BytesIO(b"inhalt"), "image/jpeg")

        assert abgelegt.size == 6
        assert store.exists(schluessel)
        with store.open(schluessel) as datei:
            assert datei.read() == b"inhalt"

        store.delete(schluessel)
        assert not store.exists(schluessel)

    def test_loeschen_eines_fehlenden_objekts_ist_kein_fehler(self, store: LocalMediaStore) -> None:
        store.delete(build_storage_key(new_id(), new_id()))

    def test_dateisystem_kann_keine_signierte_url(self, store: LocalMediaStore) -> None:
        """Gibt None zurueck; die Anwendung liefert den Inhalt selbst aus."""
        schluessel = build_storage_key(new_id(), new_id())
        assert store.create_read_url(schluessel, timedelta(minutes=5)) is None


class TestPfadAusbruch:
    @pytest.mark.parametrize(
        "boeser_schluessel",
        [
            "../ausserhalb",
            "../../etc/passwd",
            "spaces/../../../etc/passwd",
            "a/b/../../../../tmp/gekapert",
        ],
    )
    def test_schreiben_ausserhalb_wird_abgewiesen(
        self, store: LocalMediaStore, boeser_schluessel: str
    ) -> None:
        with pytest.raises(ValueError):
            store.put(boeser_schluessel, io.BytesIO(b"x"), "text/plain")

    @pytest.mark.parametrize("boeser_schluessel", ["../ausserhalb", "../../etc/passwd"])
    def test_lesen_ausserhalb_wird_abgewiesen(
        self, store: LocalMediaStore, boeser_schluessel: str
    ) -> None:
        with pytest.raises(ValueError):
            store.open(boeser_schluessel)

    def test_loeschen_ausserhalb_wird_abgewiesen(self, store: LocalMediaStore) -> None:
        with pytest.raises(ValueError):
            store.delete("../../etc/passwd")

    def test_absoluter_pfad_wird_abgewiesen(self, store: LocalMediaStore) -> None:
        """Ein absoluter Pfad ersetzt beim Zusammensetzen die Wurzel."""
        with pytest.raises(ValueError):
            store.put("/etc/gekapert", io.BytesIO(b"x"), "text/plain")

    def test_nichts_liegt_ausserhalb_der_wurzel(self, tmp_path: Path) -> None:
        wurzel = tmp_path / "media"
        store = LocalMediaStore(wurzel)
        schluessel = build_storage_key(UUID(int=1), UUID(int=2))
        store.put(schluessel, io.BytesIO(b"x"), "text/plain")

        erzeugt = [p for p in tmp_path.rglob("*") if p.is_file()]
        assert erzeugt
        assert all(p.is_relative_to(wurzel) for p in erzeugt)
