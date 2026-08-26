"""Der Wish-Slice muss den in M3-D01/D02/D05 entschiedenen Vertrag spiegeln.

Der Vertrag ist hier mehr als Formsache. Zwei Entscheidungen leben
ausschliesslich in seiner Form: dass `status` kein Feld ist, das ein Client
schreibt, und dass `createdBy` Attribution und keine ACL ist. Ein Request-
Schema, das eines von beiden durchliesse, waere der Weg am Wish->Plan-
Vertrag vorbei - und zwar bevor irgendein Dienst gefragt wird.
"""

from __future__ import annotations

from sidebyside.main import create_app

COLLECTION = "/api/v1/spaces/{spaceId}/wishes"
DETAIL = "/api/v1/spaces/{spaceId}/wishes/{wishId}"


def _schema() -> dict[str, object]:
    return create_app().openapi()


def _paths() -> dict[str, dict[str, dict]]:
    return _schema()["paths"]  # type: ignore[index,return-value]


def _components() -> dict[str, dict]:
    return _schema()["components"]["schemas"]  # type: ignore[index,return-value]


def test_wish_routes_have_frozen_operation_ids() -> None:
    paths = _paths()
    assert paths[COLLECTION]["post"]["operationId"] == "createWish"
    assert paths[COLLECTION]["get"]["operationId"] == "listWishes"
    assert paths[DETAIL]["get"]["operationId"] == "getWish"
    assert paths[DETAIL]["patch"]["operationId"] == "updateWish"
    assert paths[DETAIL]["delete"]["operationId"] == "deleteWish"


def test_the_contract_carries_exactly_the_decided_wish_surface() -> None:
    """M3-D02 nennt sechs Wish-Operationen; fuenf davon gehoeren zu M3-S1.

    `POST .../wishes/{wishId}/plan` ist die sechste. Sie fehlt hier
    absichtlich: ohne Plan-Domaene gaebe es nichts, was sie erzeugen
    koennte, und ein Vertrag, der sie schon nennt, verspricht einen Flow,
    den der Server nicht hat.
    """
    wish_paths = {pfad for pfad in _paths() if "/wishes" in pfad}
    assert wish_paths == {COLLECTION, DETAIL}


def test_mutations_require_if_match() -> None:
    detail = _paths()[DETAIL]
    for methode in ("patch", "delete"):
        namen = {parameter["name"] for parameter in detail[methode].get("parameters", [])}
        assert "If-Match" in namen
        pflicht = next(
            parameter
            for parameter in detail[methode]["parameters"]
            if parameter["name"] == "If-Match"
        )
        assert pflicht["required"] is True


def test_create_does_not_require_if_match() -> None:
    """Ein Wish, den es noch nicht gibt, hat keine Version zum Vergleichen."""
    namen = {parameter["name"] for parameter in _paths()[COLLECTION]["post"].get("parameters", [])}
    assert "If-Match" not in namen


def test_no_request_body_accepts_status_or_ownership() -> None:
    """M3-D01/D02: Status und Attribution kommen vom Server, nicht vom Client."""
    verboten = {"status", "createdBy", "spaceId", "version", "id", "createdAt", "updatedAt"}
    for name in ("WishCreate", "WishUpdate"):
        schema = _components()[name]
        assert set(schema["properties"]) & verboten == set()
        # Kein stilles Verschlucken: zusaetzliche Felder werden abgewiesen,
        # sonst glaubte ein Client, er haette den Status gesetzt.
        assert schema.get("additionalProperties") is False


def test_create_requires_only_a_title() -> None:
    schema = _components()["WishCreate"]
    assert set(schema["properties"]) == {"title"}
    assert schema["required"] == ["title"]


def test_update_offers_only_the_title() -> None:
    """Es gibt kein Feld, ueber das ein PATCH den Status setzen koennte."""
    assert set(_components()["WishUpdate"]["properties"]) == {"title"}


def test_detail_exposes_status_and_attribution_read_only() -> None:
    schema = _components()["WishDetail"]
    assert {"status", "createdBy", "creator", "capabilities"} <= set(schema["properties"])
    assert set(_components()["WishStatus"]["enum"]) == {"OPEN", "PLANNED", "COMPLETED"}


def test_detail_carries_no_wish_body() -> None:
    """Ein Wish hat in M3 nur einen Titel - `body` gehoert zum Plan."""
    assert "body" not in _components()["WishDetail"]["properties"]


def test_list_filters_by_status_and_not_by_free_text() -> None:
    """Volltextsuche ist M4-A und ausdruecklich nicht Teil von M3."""
    parameter = {p["name"] for p in _paths()[COLLECTION]["get"].get("parameters", [])}
    assert {"status", "cursor", "limit"} <= parameter
    assert "q" not in parameter


def test_conflict_is_a_documented_answer_for_every_versioned_write() -> None:
    """Ein 409 ist bei Wish nicht nur der Versionskonflikt.

    Ueber denselben Status antwortet spaeter die Delete-Matrix aus M3-D05.
    Beide muessen im Vertrag stehen, sonst behandelt ein Client den Fall
    als unerwarteten Fehler.
    """
    detail = _paths()[DETAIL]
    assert "409" in detail["patch"]["responses"]
    assert "409" in detail["delete"]["responses"]
