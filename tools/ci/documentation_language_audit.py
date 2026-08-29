#!/usr/bin/env python3
"""Audit active engineering documentation for residual German prose.

This module deliberately complements ``engineering_language_audit.py`` rather
than duplicating its source-code and identifier logic. Active documentation is
scanned with the same engineering-prose detector while frozen review snapshots,
stable repository link targets, and narrowly enumerated localized product copy
remain outside the migration boundary.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from engineering_language_audit import _contains_marker, _format_finding

DOCUMENTATION_ROOTS = (
    Path("docs"),
    Path("specification"),
    Path("design"),
)
DOCUMENTATION_SUFFIXES = {".json", ".md", ".svg"}
EXCLUDED_DOCUMENTATION_PREFIXES = (Path("docs/reviews"),)

# Path-specific values are intentionally localized user-facing copy or
# synthetic domain-content fixtures embedded in otherwise English technical
# documentation. Exact-value exceptions keep the surrounding prose audited.
ALLOWED_LOCALIZED_TEXTS_BY_PATH = {
    Path("design/m2/PLATFORM-HANDOFF.md"): (
        "Foto hinzufügen",
    ),
    Path("design/m2/SCREEN-FLOWS.md"): (
        "Moment festhalten",
        "Erinnerung",
        "Herzmoment",
        "Meilenstein",
        "Privat",
        "Mit Partner geteilt",
        "Datei wird geprüft …",
        "Foto wird verarbeitet …",
        "Nur für mich",
        "Mit Partner teilen",
        "Kommentar schreiben",
        "Wird gesendet …",
        "Offline · Stand von {Zeit}",
        "Gespeichert",
        "Synchronisiert",
        "Noch nicht gespeichert. Verbinde dich mit dem Internet und versuche es erneut.",
        "Dieser Inhalt wurde inzwischen geändert.",
    ),
    Path("design/m2/SCREEN-STATE-MATRIX.md"): (
        "Eure Story beginnt hier",
        "Erinnerung hinzufügen",
        "Keine passenden gemeinsamen Momente",
        "Filter zurücksetzen",
        "Einige Inhalte konnten nicht geladen werden.",
        "Erneut versuchen",
        "Offline · Stand von {Zeit}",
        "Erneut verbinden",
        "Noch nicht gespeichert.",
        "Fehler korrigieren",
        "Deine Sitzung ist abgelaufen.",
        "Erneut anmelden",
        "Dieser Inhalt ist nicht verfügbar.",
        "Zur Story",
        "Dieser Inhalt wurde inzwischen geändert.",
        "Aktuellen Stand ansehen",
        "Das waren viele Versuche.",
        "Das hat gerade nicht geklappt.",
        "Foto hinzufügen",
        "Noch keine Kommentare",
        "Story wird geladen",
        "Haltet einen gemeinsamen Moment fest, wenn es für euch passt.",
        "3 private Treffer ausgeblendet",
        "Wird gespeichert …",
        "Dieses Dateiformat wird nicht unterstützt.",
        "Diese Datei ist zu groß.",
        "Dieses Bild konnte nicht verarbeitet werden.",
        "Upload unterbrochen.",
        "Upload gerade nicht möglich.",
        "Nur für mich",
        "Mit Partner geteilt",
        "privat",
    ),
    Path("design/m2/m2-screenflow.svg"): (
        "Heute",
        "Planen",
        "Entdecken",
        "Mehr",
        "Moment festhalten",
    ),
    Path("docs/m2/DEMO-SCENARIO.md"): (
        "Sonnenaufgang am See",
        "Unser erster Pastateig",
        "Spaziergang im Sommerregen",
        "Danke, dass du heute einfach zugehört hast.",
        "Unser erster gemeinsamer Garten",
        "Ein Jahr in unserer Wohnung",
        "Den frühen Wecker war es wert.",
        "Nächstes Mal mit heißem Kaffee.",
        "Das bedeutet mir viel.",
        "Erinnerung",
        "Moment festhalten → Erinnerung",
        "Picknick unter den Linden",
        "Nur für mich",
        "Erste gemeinsame Bergtour",
        "Offline · Stand von …",
        "Noch nicht gespeichert",
    ),
    Path("docs/m2/SECURITY-TEST-MATRIX.md"): (
        "zuletzt geändert",
    ),
}

MARKDOWN_LINK_TARGET = re.compile(r"(?<=\]\()[^)]+(?=\))")
REPO_LOCAL_MARKDOWN_TARGET = re.compile(
    r"(?:docs|design|specification)/[A-Za-z0-9_./-]+\.md#[A-Za-z0-9_-]+"
)


def _repo_relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path


def _sanitize_documentation_text(text: str, logical_path: Path) -> str:
    sanitized = text
    for localized_text in ALLOWED_LOCALIZED_TEXTS_BY_PATH.get(logical_path, ()):
        sanitized = sanitized.replace(localized_text, "")
    sanitized = MARKDOWN_LINK_TARGET.sub("", sanitized)
    sanitized = REPO_LOCAL_MARKDOWN_TARGET.sub("", sanitized)
    return sanitized


def check_documentation_file(path: Path, repo_root: Path = Path(".")) -> list[str]:
    logical_path = _repo_relative_path(path, repo_root)
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        sanitized = _sanitize_documentation_text(line, logical_path)
        if _contains_marker(sanitized):
            finding = _format_finding(logical_path, line_number, line)
            print(finding, file=sys.stderr)
            findings.append(finding)
    return findings


def documentation_files(repo_root: Path = Path(".")) -> list[Path]:
    files: list[Path] = []
    for root in DOCUMENTATION_ROOTS:
        scoped_root = repo_root / root
        if not scoped_root.is_dir():
            continue
        for path in scoped_root.rglob("*"):
            logical_path = _repo_relative_path(path, repo_root)
            excluded = any(
                logical_path == prefix or prefix in logical_path.parents
                for prefix in EXCLUDED_DOCUMENTATION_PREFIXES
            )
            if path.is_file() and path.suffix in DOCUMENTATION_SUFFIXES and not excluded:
                files.append(path)
    return sorted(set(files))


def audit_documentation(repo_root: Path = Path(".")) -> list[str]:
    findings: list[str] = []
    for path in documentation_files(repo_root):
        findings.extend(check_documentation_file(path, repo_root))
    return findings


def main() -> int:
    findings = audit_documentation()
    if findings:
        print(
            f"Found {len(findings)} likely non-English active-documentation occurrence(s).",
            file=sys.stderr,
        )
        return 1

    print("Active engineering documentation satisfies the English-language audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
