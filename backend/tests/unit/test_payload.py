"""Die Grenze zwischen Metadaten und schuetzenswertem Inhalt.

Sie traegt in Version 1 noch keine Verschluesselung. Geprueft wird, dass
die Trennung existiert und dass der spaetere Wechsel keine Ausnahme
ausloest.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sidebyside.domain.payload import (
    CRYPTO_VERSION_CLIENT_SEALED,
    CRYPTO_VERSION_PLAINTEXT,
    ProtectedPayload,
    is_readable_by_server,
)


class MemoryPayload(ProtectedPayload):
    title: str = ""
    body: str = ""


class TestSealUnseal:
    def test_ist_verlustfrei(self) -> None:
        original = MemoryPayload(title="Nordsee", body="Es war windig.")
        assert MemoryPayload.unseal(original.seal()) == original

    def test_ergibt_json_taugliche_werte(self) -> None:
        gesiegelt = MemoryPayload(title="Nordsee", body="x").seal()
        assert gesiegelt == {"title": "Nordsee", "body": "x"}

    def test_fehlender_payload_wirft_nicht(self) -> None:
        """Nach der Umstellung wird es Zeilen geben, die der Server nicht
        lesen kann. Sie duerfen eine Liste nicht umwerfen."""
        assert MemoryPayload.unseal(None) == MemoryPayload()
        assert MemoryPayload.unseal({}) == MemoryPayload()

    def test_unbekanntes_feld_wird_abgewiesen(self) -> None:
        """Ein stillschweigend verworfenes Feld waere ein Datenverlust."""
        with pytest.raises(ValidationError):
            MemoryPayload.unseal({"title": "x", "gibt_es_nicht": 1})


class TestCryptoVersion:
    def test_version_1_ist_klartext(self) -> None:
        assert MemoryPayload.crypto_version == CRYPTO_VERSION_PLAINTEXT

    def test_server_kann_klartext_lesen(self) -> None:
        assert is_readable_by_server(CRYPTO_VERSION_PLAINTEXT)

    def test_server_kann_versiegeltes_nicht_lesen(self) -> None:
        """Abgeleitete Funktionen sollen die Zeile ueberspringen koennen,
        statt zu raten."""
        assert not is_readable_by_server(CRYPTO_VERSION_CLIENT_SEALED)
