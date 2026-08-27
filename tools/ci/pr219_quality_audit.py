#!/usr/bin/env python3
"""Temporary strict audit for residual hybrid German engineering language in PR #219."""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

TARGETS = tuple(
    Path("backend/tests/integration") / name
    for name in (
        "test_attachments.py",
        "test_auth_flows.py",
        "test_cloud_auth_flows.py",
        "test_endpoint_matrix.py",
        "test_oidc.py",
        "test_places.py",
        "test_private_authorization.py",
        "test_sessions.py",
        "test_wishes.py",
    )
)

# These stems deliberately target developer-facing German that escaped the
# authoritative audit after the first migration pass. They are not applied to
# ordinary product/protocol string literals.
IDENTIFIER_SEGMENTS = re.compile(
    r"(?:^|_)(?:hoch|verarbeite|validiert|projiziert|als|angekuendigt|scheitert|"
    r"verleiht|ungebunden(?:en)?|sperrt|macht|sofort|unsichtbar|verlangt|aktuelle|"
    r"entfernt|ermittelt|bleibt|bekommt|braucht|liefert|traegt|zeigt|trifft|"
    r"abgewiesen|angelegt|geaendert|geloescht|erstelle|fremd|unbekannt|gueltig|"
    r"ungueltig|abgelaufen|widerrufen|erneuern|schleife|grenze|familie|zeile|"
    r"geraet|konto|sitzung|anbieter|verbindung|schluessel|adresse|antwort|kopf|"
    r"pfad|welt|sende|wunsch|loeschen|aendern|statuspruefung|versionspruefung|"
    r"oeffentlich|privat|fremdschreibversuch|fehlgeformt|ressourcen)(?:_|$)",
    re.IGNORECASE,
)

PROSE = re.compile(
    r"(?:\b(?:Schwerpunkte|Statusautomat|Strippen|Clientpfad|Lieferstand|Typ|"
    r"sortierbar(?:es|er|e|en)?|Metadatum|Interna|verleiht|volle|erlaubt|"
    r"geworden|Capture timestamp|Plaintext field)\b|"
    r"\b(?:der|die|das|den|dem|des|ein|eine|einen|einem|einer|und|oder|ist|sind|"
    r"wird|werden|fuer|ueber|nicht|kein|keine|ohne|mit|wenn|sonst|auch|bei|beim|"
    r"von|vom|zum|zur|im|ins|am|auf|aus|gegen|zwischen|damit|dass|nur)\b)",
    re.IGNORECASE,
)


def engineering_strings(tree: ast.AST) -> list[tuple[int, str]]:
    values: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            value = ast.get_docstring(node, clean=False)
            if value:
                body = getattr(node, "body", [])
                line = body[0].lineno if body else getattr(node, "lineno", 1)
                values.append((line, value))
        elif isinstance(node, ast.Assert) and isinstance(node.msg, ast.Constant) and isinstance(node.msg.value, str):
            values.append((node.msg.lineno, node.msg.value))
    return values


def main() -> int:
    findings: set[tuple[str, int, str]] = set()
    for path in TARGETS:
        text = path.read_text(encoding="utf-8")
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.NAME and IDENTIFIER_SEGMENTS.search(token.string):
                findings.add((str(path), token.start[0], token.string))
            elif token.type == tokenize.COMMENT and PROSE.search(token.string):
                findings.add((str(path), token.start[0], token.string.strip()))
        tree = ast.parse(text)
        for line, value in engineering_strings(tree):
            if PROSE.search(value):
                findings.add((str(path), line, value.splitlines()[0]))

    if findings:
        print("Residual hybrid engineering language found:", file=sys.stderr)
        for path, line, value in sorted(findings):
            print(f"- {path}:{line}: {value}", file=sys.stderr)
        return 1
    print("Strict PR #219 quality audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
