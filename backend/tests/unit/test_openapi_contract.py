"""Der Contract-Check muss selbst kleine unbeabsichtigte Drifts erkennen."""

from __future__ import annotations

import pytest

from scripts.openapi_contract import ContractMismatchError, ensure_contract_matches


def test_manipulierter_vertrag_schlaegt_fehl() -> None:
    contract = {"info": {"title": "SideBySide Next"}, "openapi": "3.1.0"}
    manipulated = {**contract, "info": {"title": "Unbeabsichtigte Aenderung"}}

    with pytest.raises(ContractMismatchError, match="OpenAPI-Vertrag ist nicht aktuell"):
        ensure_contract_matches(contract, manipulated)
