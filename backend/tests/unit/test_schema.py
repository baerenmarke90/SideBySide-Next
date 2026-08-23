"""Serialisierungsgrenze: aussen camelCase, innen snake_case."""

from __future__ import annotations

from sidebyside.api.schema import ApiModel, to_camel


class Beispiel(ApiModel):
    space_id: str
    happened_on: str | None = None
    title: str = ""


class TestToCamel:
    def test_wandelt_um(self) -> None:
        assert to_camel("space_id") == "spaceId"
        assert to_camel("happened_on") == "happenedOn"
        assert to_camel("crypto_version") == "cryptoVersion"

    def test_laesst_einzelwoerter_stehen(self) -> None:
        assert to_camel("title") == "title"


class TestApiModel:
    def test_gibt_camel_case_aus(self) -> None:
        aus = Beispiel(space_id="s1", happened_on="2026-08-23").model_dump(by_alias=True)
        assert set(aus) == {"spaceId", "happenedOn", "title"}

    def test_nimmt_camel_case_entgegen(self) -> None:
        modell = Beispiel.model_validate({"spaceId": "s1", "happenedOn": "2026-08-23"})
        assert modell.space_id == "s1"

    def test_nimmt_auch_den_internen_namen(self) -> None:
        """Erleichtert das Bauen von Objekten im Python-Code."""
        assert Beispiel(space_id="s1").space_id == "s1"
