#!/usr/bin/env python3
"""Final exact cleanup for the remaining #214 engineering-language findings.

This temporary migration helper runs after the two broad codemod passes.  It
changes only the developer-facing comments, docstrings, and identifiers still
reported by the authoritative audit.  Product strings, locale fixtures, and
protocol payloads are intentionally untouched.
"""

from pathlib import Path

REPLACEMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    "backend/tests/integration/test_attachments.py": (
        (
            "Owner-Boundary and the fail-closed-Behavior bei allem, what not on the",
            "Owner boundary and fail-closed behavior for everything that is not on the",
        ),
    ),
    "backend/tests/integration/test_cloud_auth_flows.py": (
        (
            "`SBS_MAIL_TRANSPORT=none`: the Capability is missing, and the is stored in the Response.",
            "`SBS_MAIL_TRANSPORT=none`: the capability is unavailable, and the response records that state.",
        ),
        (
            "erzeugtem Token in the Database.",
            "generated token in the database.",
        ),
    ),
    "backend/tests/integration/test_endpoint_matrix.py": (
        (
            "The Invariants, the for *every* Endpoint apply must.",
            "The invariants that must apply to *every* endpoint.",
        ),
        (
            "The fachlichen Sichtbarkeitsregeln stehen bei ihrer Domaene; there gehoeren",
            "Domain-specific visibility rules live with their domain; that is where",
        ),
        (
            "other Teil: that no einziger Endpoint the Mandantenpruefung vergisst.",
            "they belong. This matrix covers the other part: no endpoint may omit tenant isolation.",
        ),
        (
            "The Unterschied is Vollstaendigkeit. A Luecke is created not dadurch,",
            "The distinction is completeness. A gap is not created because",
        ),
        (
            "Endpoint it gar not erst gets. `test_der_vertrag_ist_vollstaendig_",
            "an endpoint behaves incorrectly, but because an endpoint is missing entirely. `test_the_contract_is_complete_",
        ),
        (
            "abgedeckt` haelt the Table unten deshalb gegen the OpenAPI-Contract: a",
            "covered` therefore compares the table below with the OpenAPI contract.",
        ),
        (
            "# the unterscheidet it vom Sign in through same Provider.",
            "# This distinguishes it from sign-in through the same provider.",
        ),
    ),
    "backend/tests/integration/test_oidc.py": (
        (
            "OIDC-Sign-in gegen a mock Provider.",
            "OIDC sign-in against a mock provider.",
        ),
        (
            "richtigen RSA-Key. Damit checks the Suite the Signaturpruefung",
            "correct RSA key. This makes the suite exercise signature verification",
        ),
    ),
    "backend/tests/integration/test_places.py": (
        (
            "A Create-Body.",
            "A create request body.",
        ),
        (
            "weist a ausdrueckliches `null` ab (like bei Memory and Milestone).",
            "rejects an explicit `null` (as with Memory and Milestone).",
        ),
        (
            "A Client, the the Coordinates as Couple fuehrt, sendet both.",
            "A client that treats the coordinates as a pair sends both values.",
        ),
        (
            "Create-Contract a ausdrueckliches `null` ab, like bei Memory and",
            "The create contract rejects an explicit `null`, as with Memory and",
        ),
    ),
    "backend/tests/integration/test_private_authorization.py": (
        (
            "Owner- and Privacy-Isolation through HTTP gegen echtes PostgreSQL.",
            "Owner and privacy isolation through HTTP against real PostgreSQL.",
        ),
        (
            "The Matrix from docs/SECURITY.md, to the Eigentuemerfrage erweitert:",
            "The matrix from docs/SECURITY.md, extended with the ownership question:",
        ),
        (
            "Eigentuemer on eigene OWNER_ONLY-Row       erlaubt, therefore aendernd",
            "Owner on own OWNER_ONLY row                 allowed, including mutation",
        ),
        (
            "The Sonde from `tests.support.privacy_probe` is no Fachdomaene, sondern",
            "The probe from `tests.support.privacy_probe` is not a product domain, but",
        ),
        (
            "the duennste Resource, to the itself the Grundlage pruefen allows; siehe",
            "the thinnest resource that can exercise the underlying rule itself; see",
        ),
        (
            "the Begruendung there.",
            "the rationale there.",
        ),
        (
            "The Partner is no privileged Leser. Bei OWNER_ONLY is stored it",
            "The partner is not a privileged reader. With OWNER_ONLY the resource is",
        ),
        (
            "Leck; it war in the Speicher, in the Log and in the Antwortgroesse.",
            "leak; it would already have reached storage, logs, and response-size side channels.",
        ),
    ),
    "backend/tests/integration/test_sessions.py": (
        (
            "Geraetesitzungen.",
            "Device sessions.",
        ),
        (
            "Tested is not only the gute Fall, sondern before allem: what passiert bei",
            "The suite tests not only the happy path, but especially what happens for",
        ),
        (
            "def test_gueltiger_token_ergibt_the_account(",
            "def test_valid_token_returns_the_account(",
        ),
        (
            "Without it would be the Sitzungsdauer unbegrenzt: the gleitende Fenster",
            "Without it the session lifetime would be unbounded: the sliding window",
        ),
        (
            "Successful Rotationen are itself limited.",
            "Successful rotations are themselves limited.",
        ),
        (
            "Without Boundary could a Client with gueltigem Token in a engen",
            "Without this boundary a client with a valid token could, in a tight",
        ),
        (
            "Schleife beliebig viele Generationen and damit beliebig viele Rows",
            "loop, create arbitrarily many generations and therefore arbitrarily many rows",
        ),
    ),
    "backend/tests/integration/test_wishes.py": (
        (
            "M3-D01: a Wish belongs the Couple. Anders as bei Memory and Milestone",
            "M3-D01: a Wish belongs to the couple. Unlike Memory and Milestone",
        ),
        (
            "# Ben is intentionally Member both Spaces. Damit can the Cursor-Bindung",
            "# Ben is intentionally a member of both spaces. This lets the cursor binding",
        ),
        (
            "The Countercheck to the new Schreibregel.",
            "The countercheck for the new write rule.",
        ),
        (
            "Collaborative write is a Eigenschaft the M3-Planungsdomaenen,",
            "Collaborative write is a property of the M3 planning domains,",
        ),
        (
            "The vollstaendigen Konvertierungs- and Completion-Pfade stehen in",
            "The complete conversion and completion paths are covered in",
        ),
        (
            "def test_the_version_check_gets_before_the_statuspruefung(",
            "def test_the_version_check_runs_before_the_status_check(",
        ),
    ),
}


def main() -> int:
    missing: list[str] = []
    for filename, replacements in REPLACEMENTS.items():
        path = Path(filename)
        text = path.read_text(encoding="utf-8")
        original = text
        for source, target in replacements:
            if source not in text:
                missing.append(f"{filename}: {source}")
                continue
            text = text.replace(source, target)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"finalized {filename}")

    if missing:
        print("Expected post-codemod fragments were not found:")
        for item in missing:
            print(f"- {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
