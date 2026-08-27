#!/usr/bin/env python3
"""Document the intentionally staged engineering-language migration boundary.

This is not a natural-language detector. It guards only concrete legacy markers
that have already been audited in central developer surfaces migrated by #212.
Broad repository translation is tracked in explicit follow-up issues because a
heuristic language detector would create false positives in localization data,
quoted material, protocols, and historical snapshots.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCOPED_FILES = (
    Path("AGENTS.md"),
    Path("CONTRIBUTING.md"),
    Path("docs/ENGINEERING-LANGUAGE.md"),
    Path("docs/ENGINEERING-LANGUAGE-MIGRATION.md"),
    Path("docs/REUSE-BEFORE-BUILD.md"),
    Path(".github/pull_request_template.md"),
    Path(".github/workflows/reuse-review.yml"),
    Path("tools/openapi/generate.sh"),
    Path("tools/ci/status_drift.py"),
    Path("tools/ci/test_status_drift.py"),
)

# High-confidence legacy engineering words only. These are intentionally
# narrow; this gate must never classify arbitrary user/product text by language.
LEGACY_ENGINEERING_MARKERS = re.compile(
    r"\b(?:"
    r"Zusammenfassung|Begruendung|Begründung|Gepruefte|Geprüfte|Entscheidung|"
    r"Erzeugt|erzeugen|wurzel|vertrag|pruefmodus|Prüfmodus|abweichung|"
    r"ungueltig|ungültig|geprueft|geprüft|ausgefuehrt|ausgeführt|"
    r"abgeschwaecht|abgeschwächt|Living-Status-Datei"
    r")\b",
    re.IGNORECASE,
)

# This exact German phrase is deliberately retained as matching input in the
# status-drift migration compatibility regex and its corresponding unit test.
ALLOWED_LEGACY_INPUT = "Aktueller `main`"


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    sanitized = text.replace(ALLOWED_LEGACY_INPUT, "")
    findings: list[str] = []
    for line_number, line in enumerate(sanitized.splitlines(), start=1):
        if LEGACY_ENGINEERING_MARKERS.search(line):
            findings.append(f"{path}:{line_number}: {line.strip()}")
    return findings


def main() -> int:
    findings: list[str] = []
    for path in SCOPED_FILES:
        if not path.is_file():
            findings.append(f"{path}: required scoped file is missing")
            continue
        findings.extend(check_file(path))

    if findings:
        print("Legacy engineering-language markers found in migrated developer surfaces:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1

    print("Migrated developer surfaces satisfy the scoped English-language audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
