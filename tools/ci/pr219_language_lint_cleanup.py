#!/usr/bin/env python3
"""Fix final lint/semantic artifacts from the temporary #214 codemod."""

from pathlib import Path


def replace_required(path: Path, source: str, target: str) -> None:
    text = path.read_text(encoding="utf-8")
    if source not in text:
        raise RuntimeError(f"Expected migration fragment not found in {path}: {source!r}")
    path.write_text(text.replace(source, target), encoding="utf-8")


def replace_optional(path: Path, source: str, target: str) -> None:
    text = path.read_text(encoding="utf-8")
    if source in text:
        path.write_text(text.replace(source, target), encoding="utf-8")


def replace_module_docstring(path: Path, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith('"""'):
        raise RuntimeError(f"Expected module docstring in {path}")
    end = text.find('"""', 3)
    if end < 0:
        raise RuntimeError(f"Unterminated module docstring in {path}")
    path.write_text(replacement + text[end + 3 :], encoding="utf-8")


def main() -> int:
    cloud = Path("backend/tests/integration/test_cloud_auth_flows.py")
    replace_required(
        cloud,
        "`SBS_MAIL_TRANSPORT=none`: the capability is unavailable, and the response records that state.",
        "`SBS_MAIL_TRANSPORT=none`: the capability is unavailable, and the response\n"
        "    records that state.",
    )
    replace_optional(cloud, "schlechte Gegenentwurf", "bad counterexample")
    replace_optional(cloud, "Bestaetigung", "confirmation")
    replace_optional(cloud, "erzeugtem", "generated")

    matrix = Path("backend/tests/integration/test_endpoint_matrix.py")
    replace_module_docstring(
        matrix,
        '"""Cross-cutting endpoint invariants.\n\n'
        "Domain-specific visibility rules live with their domain. This matrix covers\n"
        "the complementary guarantee that every endpoint enforces tenant isolation.\n\n"
        "The distinction is completeness: a gap can exist because an endpoint is\n"
        "missing from the matrix entirely. `test_the_contract_is_complete_covered`\n"
        "therefore compares the table below with the OpenAPI contract. A new operation\n"
        "without an entry makes the suite fail before it reaches production.\n"
        '"""',
    )
    replace_required(matrix, 'wish = {"title": "Matrix Wish"}', 'WISH = {"title": "Matrix Wish"}')
    replace_required(
        matrix,
        'Endpoint("POST", "/api/v1/spaces/{spaceId}/wishes", body=wish)',
        'Endpoint("POST", "/api/v1/spaces/{spaceId}/wishes", body=WISH)',
    )
    replace_required(
        matrix,
        'wish = client.post(f"{basis}/wishes", json=wish, headers=headers).json()',
        'wish = client.post(f"{basis}/wishes", json=WISH, headers=headers).json()',
    )

    wishes = Path("backend/tests/integration/test_wishes.py")
    replace_required(
        wishes,
        "from sidebyside.wishes.models import wish, WishStatus",
        "from sidebyside.wishes.models import Wish, WishStatus",
    )
    replace_optional(wishes, "session.get(wish,", "session.get(Wish,")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
