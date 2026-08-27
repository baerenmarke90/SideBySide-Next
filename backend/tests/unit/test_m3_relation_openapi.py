"""Der Relations-Slice muss den in M3-D08/D09 entschiedenen Vertrag spiegeln.

Zwei Zusicherungen leben ausschliesslich in der Form des Vertrags.

Der Zieltyp steht im Pfad, nicht im Body. Es gibt keine Operation, die
einen `targetType` entgegennimmt, und keine Union in den Komponenten -
genau das trennt Option A aus `docs/m3/API-DESIGN.md` von der
`(targetType,targetId)`-Polymorphie, die M3-D08 ausschliesst.

Und: keine dieser Operationen hat einen Request Body. Eine Relation
besteht ausschliesslich aus den beiden IDs im Pfad; ein Body waere Platz
fuer ein Feld, das eine der beiden Seiten noch einmal anders benennt.
"""

from __future__ import annotations

import pytest

from sidebyside.main import create_app

SLUGS = ("memories", "heart-moments", "milestones")

PLACE_DETAIL = "/api/v1/spaces/{spaceId}/places/{placeId}"

OPERATIONEN = {
    "memories": ("listPlaceMemories", "linkPlaceMemory", "unlinkPlaceMemory"),
    "heart-moments": ("listPlaceHeartMoments", "linkPlaceHeartMoment", "unlinkPlaceHeartMoment"),
    "milestones": ("listPlaceMilestones", "linkPlaceMilestone", "unlinkPlaceMilestone"),
}


def _schema() -> dict[str, object]:
    return create_app().openapi()


def _paths() -> dict[str, dict[str, dict]]:
    return _schema()["paths"]  # type: ignore[index,return-value]


def _collection(slug: str) -> str:
    # Zusammengesetzt statt formatiert: die Vorlage traegt selbst
    # geschweifte Klammern fuer spaceId und placeId, die hier stehen
    # bleiben muessen.
    return f"{PLACE_DETAIL}/{slug}"


def _item(slug: str) -> str:
    return f"{_collection(slug)}/{{targetId}}"


@pytest.mark.parametrize("slug", SLUGS)
def test_relation_routes_have_frozen_operation_ids(slug: str) -> None:
    paths = _paths()
    liste, verknuepfen, loesen = OPERATIONEN[slug]
    assert paths[_collection(slug)]["get"]["operationId"] == liste
    assert paths[_item(slug)]["put"]["operationId"] == verknuepfen
    assert paths[_item(slug)]["delete"]["operationId"] == loesen


@pytest.mark.parametrize("slug", SLUGS)
def test_relation_writes_have_no_request_body(slug: str) -> None:
    item = _paths()[_item(slug)]
    for methode in ("put", "delete"):
        assert "requestBody" not in item[methode], methode


@pytest.mark.parametrize("slug", SLUGS)
def test_relation_writes_answer_204(slug: str) -> None:
    """`PUT` ist idempotent und unterscheidet nicht nach Vorzustand.

    Kein `201` gegen `200`: der Unterschied waere eine Auskunft darueber,
    was ein anderes Geraet kurz zuvor getan hat.
    """
    item = _paths()[_item(slug)]
    for methode in ("put", "delete"):
        assert "204" in item[methode]["responses"], methode
        assert "200" not in item[methode]["responses"], methode
        assert "201" not in item[methode]["responses"], methode


def test_no_operation_takes_a_target_type_discriminator() -> None:
    """Der Gegentest zu Option B aus `docs/m3/API-DESIGN.md`.

    Kein Pfad, kein Parameter und kein Schemafeld benennt einen Zieltyp.
    Waere hier je ein `targetType` erlaubt, waere die Allowlist nicht mehr
    der Vertrag, sondern eine Laufzeitpruefung dahinter.
    """
    schema = _schema()
    relationspfade = {
        pfad: operationen
        for pfad, operationen in schema["paths"].items()  # type: ignore[union-attr]
        if "/places/{placeId}/" in pfad
    }
    assert relationspfade, "keine Relationsrouten im Vertrag"

    for pfad, operationen in relationspfade.items():
        for methode, operation in operationen.items():
            namen = {p["name"] for p in operation.get("parameters", [])}
            assert "targetType" not in namen, f"{methode} {pfad}"
            assert "relation" not in namen, f"{methode} {pfad}"

    assert "targetType" not in str(schema["components"])


def test_relation_reads_return_ids_only() -> None:
    """Die Liste liefert IDs und keine Inhalte.

    Eine Relationsliste, die Titel oder Text mitliefert, waere ein zweiter
    Leseweg mit eigener Autorisierung - und zwei Lesewege driften.
    """
    komponenten = _schema()["components"]["schemas"]  # type: ignore[index]
    ziele = komponenten["RelationTargets"]
    assert set(ziele["properties"]) == {"items"}
    assert ziele["properties"]["items"]["items"]["format"] == "uuid"
