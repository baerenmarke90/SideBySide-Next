"""Gebundene Parameter duerfen nicht ins Anwendungslog geraten.

Die Anwendung protokolliert unbehandelte Fehler mit `log.exception`. Ohne
`hide_parameters` schreibt SQLAlchemy die gebundenen Werte in jede
Datenbank-Fehlermeldung - und damit genau das in das Log, was hinter der
ProtectedPayload-Grenze liegen soll: Titel, Texte, Adressen und die
Koordinaten eines Ortes.

M3-D28 verbietet Ortsdaten in Logs ausdruecklich. Fuer die uebrigen
geschuetzten Inhalte gilt dasselbe seit M2, es stand nur nirgends fest.
"""

from __future__ import annotations

from sqlalchemy import Engine

from sidebyside.db.session import get_engine


def _engine() -> Engine:
    return get_engine()


def test_die_engine_verschweigt_gebundene_parameter() -> None:
    assert _engine().hide_parameters is True


def test_eine_datenbankfehlermeldung_traegt_keine_werte() -> None:
    """Die Gegenprobe an einem echten Fehlertext.

    Kein Datenbankzugriff noetig: SQLAlchemy entscheidet beim Bauen der
    Fehlermeldung, ob die Parameter mitgehen.
    """
    from sqlalchemy.exc import StatementError

    fehler = StatementError(
        "boom",
        "INSERT INTO places (latitude, longitude) VALUES (%(lat)s, %(lon)s)",
        {"lat": "52.520008", "lon": "13.404954"},
        Exception("boom"),
        hide_parameters=_engine().hide_parameters,
    )
    text = str(fehler)
    assert "52.520008" not in text
    assert "13.404954" not in text
    assert "SQL parameters hidden" in text
