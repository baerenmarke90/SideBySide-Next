#!/usr/bin/env python3
"""Guard the staged English engineering-language migration boundary.

This is deliberately not a generic language detector. For Python in the #214
backend scope it checks engineering surfaces only: identifiers, comments,
docstrings, assertions, and developer/runtime diagnostics. Ordinary string
literals are deliberately excluded because they can be product, localization,
protocol, persistence, or historical contract data.
"""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
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

# Common German grammar is safe to use for comments/docstrings because those
# are engineering prose. The additional stems catch transliterated legacy
# identifiers that contain compounds rather than standalone words.
ENGINEERING_PROSE_MARKERS = re.compile(
    r"(?:"
    r"\b(?:der|die|das|den|dem|des|ein|eine|einen|einem|einer|ist|sind|wird|"
    r"werden|wurde|wurden|und|oder|ohne|mit|nicht|kein|keine|keinen|nur|wenn|"
    r"damit|dass|sonst|auch|dieser|diese|dieses|hier|dort|als|bei|beim|vom|"
    r"von|zum|zur|im|ins|am|an|auf|aus|gegen|zwischen|bereits|immer|spaeter|"
    r"später|fuer|für|ueber|über|wuerde|würde|koennte|könnte|koennen|können|"
    r"muessen|müssen|muesste|müsste|zurueck|zurück)\b|"
    r"(?:pruef|prüf|guelt|gült|unguelt|ungült|laesst|lässt|enthaelt|enthält|"
    r"abhaeng|abhäng|zulaess|zuläss|benoet|benöt|verschluessel|verschlüssel|"
    r"schluessel|schlüssel|eigentuemer|eigentümer|domaene|domäne|bedingung|"
    r"durchsetz|speicherbar|vollstaendig|vollständig|unveraendert|unverändert|"
    r"fehler|antwort|anbieter|gegenstelle|anmeldung|konto|sitzung|verbindung|"
    r"erzeugt|geaendert|geändert|pruefung|prüfung|wurzel|vertrag|abweichung)"
    r")",
    re.IGNORECASE,
)

IDENTIFIER_MARKERS = re.compile(
    r"(?:"
    r"(?:^|_)(?:der|die|das|ein|eine|ist|sind|wird|ohne|mit|nicht|kein|keine|"
    r"fuer|ueber|zurueck|antwort|fehler|anbieter|gegenstelle|anmeldung|konto|"
    r"sitzung|verbindung|schluessel|pruefung|wurzel|vertrag|erzeugt|geaendert|"
    r"unveraendert|welt|ort|plaene|erinnerung|moment|meldungen|geheimnis)(?:_|$)|"
    r"(?:schluessel|pruefung|ueberschreib|oeffentlich|begonnen|identitaet|"
    r"verknuepf|abgelehnt|unbekannt|falsch|gueltig|ungueltig|zurueck|"
    r"vollstaendig|unveraendert|erzeugt|geaendert)"
    r")",
    re.IGNORECASE,
)

# This exact German phrase is deliberately retained as matching input in the
# status-drift migration compatibility regex and its corresponding unit test.
ALLOWED_LEGACY_INPUT = "Aktueller `main`"

DIAGNOSTIC_CALLS = {"print", "fail", "skip", "xfail"}
DIAGNOSTIC_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}


def _format_finding(path: Path, line_number: int, text: str) -> str:
    return f"{path}:{line_number}: {text.strip()}"


def _contains_marker(text: str) -> bool:
    return ENGINEERING_PROSE_MARKERS.search(text.replace(ALLOWED_LEGACY_INPUT, "")) is not None


def _literal_strings(node: ast.AST | None) -> list[tuple[int, str]]:
    if node is None:
        return []
    values: list[tuple[int, str]] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.append((child.lineno, child.value))
    return values


def _call_name(call: ast.Call) -> tuple[str | None, str | None]:
    if isinstance(call.func, ast.Name):
        return call.func.id, None
    if isinstance(call.func, ast.Attribute):
        return None, call.func.attr
    return None, None


def check_python_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings: set[tuple[int, str]] = set()

    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type == tokenize.COMMENT and _contains_marker(token.string):
                findings.add((token.start[0], token.string))
            elif token.type == tokenize.NAME and IDENTIFIER_MARKERS.search(token.string):
                findings.add((token.start[0], token.string))
    except tokenize.TokenError:
        # Syntax/format checks will report malformed Python separately. Keep the
        # language audit useful rather than masking the primary error.
        pass

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [_format_finding(path, line, value) for line, value in sorted(findings)]

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node, clean=False)
            if docstring and _contains_marker(docstring):
                body = getattr(node, "body", [])
                line_number = body[0].lineno if body else getattr(node, "lineno", 1)
                findings.add((line_number, docstring.splitlines()[0]))

        if isinstance(node, ast.Assert):
            for line_number, value in _literal_strings(node.msg):
                if _contains_marker(value):
                    findings.add((line_number, value))

        if isinstance(node, ast.Raise):
            for line_number, value in _literal_strings(node.exc):
                if _contains_marker(value):
                    findings.add((line_number, value))

        if isinstance(node, ast.Call):
            name, method = _call_name(node)
            is_exception = bool(name and (name.endswith("Error") or name.endswith("Exception")))
            is_diagnostic = name in DIAGNOSTIC_CALLS or method in DIAGNOSTIC_METHODS or is_exception
            if is_diagnostic:
                for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
                    for line_number, value in _literal_strings(argument):
                        if _contains_marker(value):
                            findings.add((line_number, value))
            if method == "raises":
                for keyword in node.keywords:
                    if keyword.arg == "match":
                        for line_number, value in _literal_strings(keyword.value):
                            if _contains_marker(value):
                                findings.add((line_number, value))

    return [
        _format_finding(path, line_number, lines[line_number - 1] if 0 < line_number <= len(lines) else value)
        for line_number, value in sorted(findings)
    ]


def check_text_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").replace(ALLOWED_LEGACY_INPUT, "")
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if _contains_marker(line):
            findings.append(_format_finding(path, line_number, line))
    return findings


def check_file(path: Path) -> list[str]:
    return check_python_file(path) if path.suffix == ".py" else check_text_file(path)


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
