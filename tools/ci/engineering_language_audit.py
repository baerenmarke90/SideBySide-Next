#!/usr/bin/env python3
"""Guard the staged English engineering-language migration boundary.

This is deliberately not a generic language detector. It checks concrete
legacy engineering markers in the developer surfaces migrated by #212 and in
the backend scope migrated by #214. Product/i18n content, protocol values, and
historical contract data are not classified merely because they are German.
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
    Path("docs/ENGINEERING-LANGUAGE-FOLLOWUPS.md"),
    Path("docs/REUSE-BEFORE-BUILD.md"),
    Path(".github/pull_request_template.md"),
    Path(".github/workflows/reuse-review.yml"),
    Path("tools/openapi/generate.sh"),
    Path("tools/ci/status_drift.py"),
    Path("tools/ci/test_status_drift.py"),
)

BACKEND_ROOTS = (
    Path("backend/src/sidebyside"),
    Path("backend/scripts"),
    Path("backend/alembic"),
    Path("backend/tests"),
)

BACKEND_SUFFIXES = {".py", ".md", ".ini", ".toml", ".txt", ".sh"}
BACKEND_FILENAMES = {"Dockerfile"}

# High-confidence legacy engineering words/stems only. The ASCII forms are
# especially useful because the original backend comments and identifiers
# commonly transliterated umlauts. Avoid broad words such as "für" or "nicht"
# that could legitimately occur in product/localization fixtures.
LEGACY_ENGINEERING_MARKERS = re.compile(
    r"(?:"
    r"\b(?:Zusammenfassung|Begruendung|Begründung|Gepruefte|Geprüfte|Entscheidung|"
    r"Erzeugt|erzeugen|wurzel|vertrag|pruefmodus|Prüfmodus|abweichung|"
    r"ungueltig|ungültig|geprueft|geprüft|ausgefuehrt|ausgeführt|"
    r"abgeschwaecht|abgeschwächt|Living-Status-Datei)\b|"
    r"\b(?:fuer|ueber|wuerde|koennte|koennen|muessen|muesste|zurueck|"
    r"pruef(?:t|en|ung)?|gueltig|ungueltig|laesst|enthaelt|abhaengig|"
    r"zulaessig|benoetigt|verschluessel(?:t|ung)?|schluessel|"
    r"eigentuemer|domaene|bedingung|durchsetzbar|speicherbar|"
    r"vollstaendig|unveraendert|ausnahm(?:e|en)|fehler)\b|"
    r"\b(?:zurück|prüf(?:t|en|ung)?|gültig|ungültig|lässt|enthält|abhängig|"
    r"zulässig|benötigt|verschlüssel(?:t|ung)?|schlüssel|Eigentümer|Domäne|"
    r"Bedingung|durchsetzbar|vollständig|unverändert)\b"
    r")",
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


def backend_files() -> list[Path]:
    files: list[Path] = []
    for root in BACKEND_ROOTS:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file() and (path.suffix in BACKEND_SUFFIXES or path.name in BACKEND_FILENAMES):
                files.append(path)
    dockerfile = Path("backend/Dockerfile")
    if dockerfile.is_file():
        files.append(dockerfile)
    return sorted(set(files))


def main() -> int:
    findings: list[str] = []
    for path in SCOPED_FILES:
        if not path.is_file():
            findings.append(f"{path}: required scoped file is missing")
            continue
        findings.extend(check_file(path))

    for path in backend_files():
        findings.extend(check_file(path))

    if findings:
        print("Legacy engineering-language markers found in migrated developer surfaces:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1

    print("Migrated developer and backend surfaces satisfy the scoped English-language audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
