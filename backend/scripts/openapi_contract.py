"""Erzeugt und prueft den versionierten OpenAPI-Vertrag der echten ASGI-App."""

from __future__ import annotations

import argparse
import difflib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from sidebyside.main import app


class ContractMismatchError(RuntimeError):
    """Der versionierte Vertrag weicht vom aktuellen API-Schema ab."""


def canonical_json(schema: Mapping[str, Any]) -> str:
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def current_contract() -> dict[str, Any]:
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    response.raise_for_status()
    schema: dict[str, Any] = response.json()
    return schema


def ensure_contract_matches(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    expected_name: str = "versionierter Vertrag",
) -> None:
    if expected == actual:
        return
    difference = "".join(
        difflib.unified_diff(
            canonical_json(expected).splitlines(keepends=True),
            canonical_json(actual).splitlines(keepends=True),
            fromfile=expected_name,
            tofile="aktuelle API",
        )
    )
    raise ContractMismatchError(f"OpenAPI-Vertrag ist nicht aktuell:\n{difference}")


def check_contract(contract_path: Path, actual: Mapping[str, Any]) -> None:
    expected: dict[str, Any] = json.loads(contract_path.read_text(encoding="utf-8"))
    ensure_contract_matches(expected, actual, expected_name=str(contract_path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("write", "check"))
    parser.add_argument("--contract", type=Path, default=Path("openapi.json"))
    arguments = parser.parse_args()
    actual = current_contract()

    if arguments.mode == "write":
        arguments.contract.write_text(canonical_json(actual), encoding="utf-8", newline="\n")
        print(f"OpenAPI-Vertrag geschrieben: {arguments.contract}")
        return 0

    try:
        check_contract(arguments.contract, actual)
    except ContractMismatchError as error:
        print(error)
        # Voruebergehend fuer die Aktualisierung des versionierten Vertrags:
        # CI ist die autoritative Laufzeitumgebung und gibt den exakt dort
        # erzeugten kanonischen Vertrag aus. Nach dem Sync wird dieser Block
        # im selben Issue wieder entfernt.
        print("--- BEGIN GENERATED OPENAPI ---")
        print(canonical_json(actual), end="")
        print("--- END GENERATED OPENAPI ---")
        return 1
    print("OpenAPI-Vertrag stimmt mit der aktuellen API ueberein.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
