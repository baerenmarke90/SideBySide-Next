"""Identifikatoren."""

from __future__ import annotations

from uuid import UUID

from sidebyside.core.ids import new_id, parse_id


class TestNewId:
    def test_liefert_eine_uuid_der_version_7(self) -> None:
        assert new_id().version == 7

    def test_ist_eindeutig(self) -> None:
        assert len({new_id() for _ in range(1000)}) == 1000

    def test_ist_zeitlich_sortierbar(self) -> None:
        """Die Sortierbarkeit ist der Grund fuer v7 statt v4.

        Ohne sie bricht der Primaerschluesselindex bei jedem Insert an einer
        zufaelligen Stelle auf.
        """
        ids = [new_id() for _ in range(100)]
        assert ids == sorted(ids)


class TestParseId:
    def test_liest_eine_gueltige_uuid(self) -> None:
        original = new_id()
        assert parse_id(str(original)) == original

    def test_gibt_none_statt_einer_ausnahme(self) -> None:
        """Eine fehlgeformte ID aus einer Anfrage ist ein erwarteter Fall.

        Sie muss zu einer sauberen Antwort fuehren, nicht zu einem 500.
        """
        for unfug in ["", "nope", "12345", "../../etc/passwd", "' OR 1=1 --"]:
            assert parse_id(unfug) is None

    def test_vertraegt_falsche_typen(self) -> None:
        assert parse_id(None) is None  # type: ignore[arg-type]
        assert parse_id(42) is None  # type: ignore[arg-type]

    def test_nimmt_auch_die_form_ohne_bindestriche(self) -> None:
        original = new_id()
        assert parse_id(original.hex) == original
        assert isinstance(parse_id(original.hex), UUID)
