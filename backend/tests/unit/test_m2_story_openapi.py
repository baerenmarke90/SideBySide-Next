"""Der Story-Slice muss den in #70 freigegebenen Vertrag spiegeln.

Story ist der einzige M2-Endpunkt, dessen Antwort eine Union ist. Wenn der
Vertrag hier abweicht, merkt das kein Client zur Laufzeit - er bekommt
einfach ein Feld nicht, das er erwartet hat.
"""

from __future__ import annotations

import json
from pathlib import Path

from sidebyside.main import create_app

TIMELINE = "/api/v1/spaces/{spaceId}/timeline"
CONTRACT = Path(__file__).parents[3] / "docs" / "m2" / "API-CONTRACT.json"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def _operation() -> dict[str, object]:
    return _schema()["paths"][TIMELINE]["get"]  # type: ignore[index,return-value]


def test_route_und_operation_id_sind_eingefroren() -> None:
    assert _operation()["operationId"] == "getStoryTimeline"


def test_query_entspricht_dem_manifest() -> None:
    manifest = json.loads(CONTRACT.read_text(encoding="utf-8"))
    eintrag = next(
        operation
        for operation in manifest["operations"]
        if operation["operationId"] == "getStoryTimeline"
    )
    namen = {
        parameter["name"]
        for parameter in _operation()["parameters"]  # type: ignore[index]
        if parameter["in"] == "query"
    }
    assert namen == set(eintrag["query"])


def test_kein_visibility_parameter() -> None:
    """M2-D22: die Story hat keinen Owner-Modus, auch nicht als Filter."""
    namen = {
        parameter["name"]
        for parameter in _operation()["parameters"]  # type: ignore[index]
    }
    assert "visibility" not in namen


def test_kein_q_parameter() -> None:
    """M2-D08 hat die Volltextsuche nach M4-A verschoben."""
    namen = {
        parameter["name"]
        for parameter in _operation()["parameters"]  # type: ignore[index]
    }
    assert "q" not in namen


def test_union_heisst_story_item() -> None:
    """`API-DESIGN.md` nennt den Typ so - der Vertrag muss ihn benennen.

    Ohne eigenen Typ nennt OpenAPI die Union nach ihrem Fundort
    (`StoryPageItemsInner`), und jeder erzeugte Client traegt diesen Namen
    weiter in Web- und Android-Code.
    """
    schemas = _schema()["components"]["schemas"]  # type: ignore[index]
    assert schemas["StoryPage"]["properties"]["items"]["items"] == {
        "$ref": "#/components/schemas/StoryItem"
    }
    assert "StoryPageItemsInner" not in schemas


def test_union_ist_ueber_kind_diskriminiert() -> None:
    schemas = _schema()["components"]["schemas"]  # type: ignore[index]
    diskriminator = schemas["StoryItem"]["discriminator"]
    assert diskriminator["propertyName"] == "kind"
    assert set(diskriminator["mapping"]) == {"MEMORY", "HEART_MOMENT", "MILESTONE"}


def test_story_kennt_keine_private_variante() -> None:
    """Die Union hat drei Varianten - eine private HeartMoment-Form gibt es nicht."""
    schemas = _schema()["components"]["schemas"]  # type: ignore[index]
    assert "visibility" not in schemas["SharedHeartMomentSummary"]["properties"]


def test_limit_und_year_tragen_die_vertraglichen_grenzen() -> None:
    parameter = {
        eintrag["name"]: eintrag
        for eintrag in _operation()["parameters"]  # type: ignore[index]
    }
    assert parameter["limit"]["schema"]["default"] == 50
    assert parameter["limit"]["schema"]["maximum"] == 100
    jahr = parameter["year"]["schema"]
    grenzen = jahr if "minimum" in jahr else next(o for o in jahr["anyOf"] if "minimum" in o)
    assert grenzen["minimum"] == 1900
    assert grenzen["maximum"] == 2100
