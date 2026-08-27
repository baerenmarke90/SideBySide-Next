#!/usr/bin/env python3
"""Second-pass cleanup for the temporary PR #219 language migration.

The first pass performs domain-oriented translations. This pass removes the
remaining German grammar and compound identifiers reported by the repository's
authoritative engineering-language audit. It is temporary migration tooling
and is removed by the one-shot workflow after successful validation.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

TARGETS = (
    Path("backend/tests/integration/test_attachments.py"),
    Path("backend/tests/integration/test_auth_flows.py"),
    Path("backend/tests/integration/test_cloud_auth_flows.py"),
    Path("backend/tests/integration/test_endpoint_matrix.py"),
    Path("backend/tests/integration/test_oidc.py"),
    Path("backend/tests/integration/test_places.py"),
    Path("backend/tests/integration/test_private_authorization.py"),
    Path("backend/tests/integration/test_sessions.py"),
    Path("backend/tests/integration/test_wishes.py"),
)

IDENTIFIER_SEGMENTS = {
    "abfragen": "queries",
    "abgeschlossen": "completed",
    "abgeschlossenen": "completed",
    "ablaufdatum": "expiry_date",
    "adressbestaetigung": "address_verification",
    "alle": "all",
    "allererste": "first",
    "am": "at",
    "an": "to",
    "anforderung": "request",
    "antwortet": "responds",
    "auf": "on",
    "begrenzt": "limits",
    "begonnene": "started",
    "beider": "both",
    "beim": "at",
    "beiden": "both",
    "bewusst": "intentionally",
    "bis": "until",
    "da": "there",
    "das": "the",
    "datenbank": "database",
    "den": "the",
    "denselben": "same",
    "der": "the",
    "des": "the",
    "die": "the",
    "domaene": "domain",
    "eines": "of_a",
    "einem": "a",
    "einen": "a",
    "einer": "a",
    "ereignis": "event",
    "erkannt": "detected",
    "ersten": "first",
    "familie": "family",
    "falsches": "wrong",
    "fenster": "window",
    "frist": "retention_period",
    "ganz": "completely",
    "geholt": "loaded",
    "geloeschten": "deleted",
    "geplant": "planned",
    "gilt": "applies",
    "gibt": "exposes",
    "grund": "reason",
    "halben": "partial",
    "hatte": "had",
    "identitaet": "identity",
    "in": "in",
    "invarianten": "invariants",
    "je": "each",
    "jetzt": "now",
    "laeuft": "continues",
    "leeres": "empty",
    "mehr": "more",
    "mitglied": "member",
    "monate": "months",
    "nennt": "names",
    "neuen": "new",
    "nutzer": "user",
    "paar": "couple",
    "pflichtparameter": "required_parameters",
    "preis": "exposed",
    "privilegierter": "privileged",
    "ressourcen": "resources",
    "rueckbau": "cleanup",
    "seinem": "its",
    "seinen": "its",
    "sie": "it",
    "signatur": "signature",
    "sonden": "probes",
    "sperrten": "would_lock",
    "statt": "instead",
    "stelle": "set_time",
    "stellbare": "controllable",
    "tippfehler": "typos",
    "traeger": "carrier",
    "trifft": "matches",
    "typisierten": "typed",
    "und": "and",
    "ununterscheidbar": "indistinguishable",
    "unter": "under",
    "verbotenes": "forbidden_value",
    "versionspruefung": "version_check",
    "vollstaendige": "complete",
    "vorbei": "bypass",
    "wege": "paths",
    "wissen": "knowledge",
    "wish": "wish",
    "zeilen": "rows",
    "zeigt": "shows",
    "zu": "to",
    "zurueckgegeben": "returned",
    "zustand": "state",
}

PROSE_WORDS = {
    "Abnahme": "acceptance tests",
    "Adressbestaetigung": "address verification",
    "Antwort": "response",
    "Antworten": "responses",
    "Bedingung": "condition",
    "Client": "client",
    "Countercheck": "countercheck",
    "Datenbank": "database",
    "Dienst": "service",
    "Endpunkt": "endpoint",
    "Endpunkte": "endpoints",
    "Faehigkeit": "capability",
    "Familie": "family",
    "Feld": "field",
    "Foreign": "foreign",
    "Getrennte": "separate",
    "Invarianten": "invariants",
    "Koordinate": "coordinate",
    "Koordinaten": "coordinates",
    "Kern": "core",
    "Lifecycles": "lifecycle",
    "Link": "link",
    "Message": "message",
    "Mitglied": "member",
    "Nutzer": "user",
    "Orte": "places",
    "Paares": "couple",
    "Paar": "couple",
    "Pfad": "path",
    "Plan": "plan",
    "Provider": "provider",
    "Resource": "resource",
    "Resources": "resources",
    "Rueckbau": "cleanup",
    "Sache": "matter",
    "Session": "session",
    "Sitzungsmodul": "session module",
    "Tabellen": "tables",
    "Target": "target",
    "Token": "token",
    "Traeger": "carrier",
    "Weg": "path",
    "Wege": "paths",
    "Wish": "wish",
    "Wissen": "knowledge",
    "Zeilen": "rows",
    "Zustand": "state",
    "abgeschlossen": "completed",
    "abgeschlossenen": "completed",
    "als": "as",
    "also": "therefore",
    "am": "at the",
    "an": "to",
    "and": "and",
    "anderen": "other",
    "anforderung": "request",
    "antwortet": "responds",
    "auf": "on",
    "begrenzt": "limited",
    "beider": "both",
    "beide": "both",
    "beim": "at",
    "beiden": "both",
    "bewusst": "intentionally",
    "bis": "until",
    "da": "there",
    "das": "the",
    "den": "the",
    "denselben": "same",
    "der": "the",
    "des": "the",
    "die": "the",
    "dort": "there",
    "echt": "real",
    "echten": "real",
    "eines": "of a",
    "einem": "a",
    "einen": "a",
    "einer": "a",
    "enden": "end",
    "ersten": "first",
    "falls": "if",
    "fuer": "for",
    "ganz": "entirely",
    "gebe": "exist",
    "geben": "exist",
    "geholt": "loaded",
    "geloeschte": "deleted",
    "geprueft": "tested",
    "gilt": "applies",
    "gelten": "apply",
    "gibt": "exists",
    "grund": "reason",
    "hatte": "had",
    "halben": "partial",
    "ihr": "their",
    "ihn": "it",
    "in": "in",
    "initial": "initially",
    "je": "each",
    "jetzt": "now",
    "kann": "can",
    "laeuft": "continues",
    "liegt": "lies",
    "mehr": "more",
    "mit": "with",
    "monate": "months",
    "nachgebauten": "mock",
    "nachgebauter": "mock",
    "neuen": "new",
    "nennte": "would name",
    "not": "not",
    "ohnehin": "already",
    "only": "only",
    "preis": "exposed",
    "privilegierter": "privileged",
    "reicht": "is sufficient",
    "selbst": "itself",
    "seinem": "its",
    "seinen": "its",
    "sie": "it",
    "sperrten": "would lock",
    "statt": "instead of",
    "steuerbaren": "controllable",
    "traegt": "grants access",
    "trifft": "matches",
    "trotzdem": "nevertheless",
    "typisierten": "typed",
    "und": "and",
    "unter": "under",
    "verbotenes": "forbidden value",
    "vollstaendige": "complete",
    "vorbei": "bypass",
    "vorher": "beforehand",
    "was": "what",
    "werden": "become",
    "wie": "like",
    "wurde": "was",
    "wuerde": "would",
    "zaehlt": "counts",
    "zeigt": "shows",
    "zu": "to",
    "zur": "to the",
}

EXACT_PHRASES = {
    "PostgreSQL-/HTTP-Abnahme for the ersten Media-Slice.": "PostgreSQL/HTTP acceptance tests for the first media slice.",
    "PostgreSQL-/HTTP-Abnahme for the M3-S3-Place-Slice.": "PostgreSQL/HTTP acceptance tests for the M3-S3 place slice.",
    "PostgreSQL-/HTTP-Abnahme for the M3-S1-Wish-Slice.": "PostgreSQL/HTTP acceptance tests for the M3-S1 wish slice.",
    "Registrierung, Sign-in und Missbrauchsschutz; through the Endpoints.": "Registration, sign-in, and abuse protection through the endpoints.",
    "Magic Link, Adressbestaetigung und Account Recovery; through the Endpoints.": "Magic link, address verification, and account recovery through the endpoints.",
    "The Message enthaelt no Link": "The message contains no link",
    "Otherwise sperrten Tippfehler the legitimate Nutzer from.": "Otherwise typos would lock out the legitimate user.",
    "Getrennte Tabellen statt a Check: the Token is dort not gesucht.": "Separate tables instead of a check: the token is not searched there.",
    "A Endpoint und das, was a Request an ihn requires.": "An endpoint and what a request to it requires.",
    "A Paar with je a echten Resource pro Domaene, plus a Foreign.": "A couple with one real resource per domain, plus a foreign one.",
    "In the eigenen Space decides the Resources-ID; und reveals nothing.": "Within the actor's own space, the resource ID decides and reveals nothing.",
    "A nachgebauter Identitaetsanbieter with steuerbaren Antworten.": "A mock identity provider with controllable responses.",
    "M3-D01 gilt for Place wie for Wish und Plan.": "M3-D01 applies to Place, Wish, and Plan alike.",
    "Viele Orte eines Paares are a Name und otherwise nothing.": "Many places belonging to a couple are only a name and nothing else.",
    "Otherwise would be das PATCH the Weg to the halben Koordinate.": "Otherwise PATCH would provide a path to a partial coordinate.",
    "The Foreign key als Boundary, falls the Dienst once fails.": "The foreign key is the boundary if the service ever fails.",
    "Malformed, unknown und fremd-privat ergeben dieselbe Antwort.": "Malformed, unknown, and foreign-private resources produce the same response.",
    "The Tenant Guard antwortet zuerst; here fails schon the Pfad.": "The tenant guard responds first; the path already fails here.",
    "A stellbare Uhr for das Sitzungsmodul.": "A controllable clock for the session module.",
    "Otherwise nennte the Antwort a Ablaufdatum, das not gilt.": "Otherwise the response would name an expiry date that does not apply.",
    "M3-D02/D04: no Weg am Wish->Plan-Contract vorbei.": "M3-D02/D04: no path bypasses the Wish-to-Plan contract.",
    "A gueltiges Feld may no Traeger for a verbotenes be.": "A valid field must not carry a forbidden value.",
    "A Zustand, the it not geben may; und trotzdem no 500.": "A state that must not exist still must not produce a 500 response.",
}

WORD_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(map(re.escape, PROSE_WORDS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def preserve_case(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


def translate_identifier(name: str) -> str:
    parts = name.split("_")
    output: list[str] = []
    changed = False
    for part in parts:
        replacement = IDENTIFIER_SEGMENTS.get(part.lower())
        if replacement is None:
            output.append(part)
            continue
        output.extend(replacement.split("_"))
        changed = True
    return "_".join(output) if changed else name


def translate_prose(text: str) -> str:
    prefix = ""
    body = text
    if body.startswith("#"):
        prefix = "#"
        body = body[1:]

    for source, target in EXACT_PHRASES.items():
        body = body.replace(source, target)

    def replace(match: re.Match[str]) -> str:
        source = match.group(0)
        target = next(value for key, value in PROSE_WORDS.items() if key.lower() == source.lower())
        return preserve_case(source, target)

    body = WORD_PATTERN.sub(replace, body)
    return prefix + body


def engineering_string_ranges(tree: ast.AST) -> set[tuple[int, int, int, int]]:
    ranges: set[tuple[int, int, int, int]] = set()

    def add(node: ast.AST | None) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            ranges.add((node.lineno, node.col_offset, node.end_lineno or node.lineno, node.end_col_offset or 0))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr):
                add(body[0].value)
        elif isinstance(node, ast.Assert):
            add(node.msg)
        elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            for argument in node.exc.args:
                add(argument)
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else None
            method = node.func.attr if isinstance(node.func, ast.Attribute) else None
            if name in {"print", "fail", "skip", "xfail"} or method in {
                "debug",
                "info",
                "warning",
                "error",
                "exception",
                "critical",
            }:
                for argument in node.args:
                    add(argument)
            if method == "raises":
                for keyword in node.keywords:
                    if keyword.arg == "match":
                        add(keyword.value)
    return ranges


def in_range(token: tokenize.TokenInfo, ranges: set[tuple[int, int, int, int]]) -> bool:
    sl, sc = token.start
    el, ec = token.end
    return any(sl >= rsl and el <= rel and (sl > rsl or sc >= rsc) and (el < rel or ec <= rec) for rsl, rsc, rel, rec in ranges)


def rewrite_string_literal(token_text: str) -> str:
    try:
        value = ast.literal_eval(token_text)
    except (SyntaxError, ValueError):
        return token_text
    if not isinstance(value, str):
        return token_text
    translated = translate_prose(value)
    if translated == value:
        return token_text
    if "\n" in translated:
        return '"""' + translated.replace('"""', '\\"\\"\\"') + '"""'
    return '"' + translated.replace("\\", "\\\\").replace('"', '\\"') + '"'


def migrate(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    tree = ast.parse(original)
    ranges = engineering_string_ranges(tree)
    output: list[tokenize.TokenInfo] = []

    for token in tokenize.generate_tokens(io.StringIO(original).readline):
        value = token.string
        if token.type == tokenize.NAME:
            value = translate_identifier(value)
        elif token.type == tokenize.COMMENT:
            value = translate_prose(value)
        elif token.type == tokenize.STRING and in_range(token, ranges):
            value = rewrite_string_literal(value)
        output.append(token._replace(string=value))

    rewritten = tokenize.untokenize(output)
    if rewritten != original:
        path.write_text(rewritten, encoding="utf-8")
        print(f"cleaned {path}")


def main() -> int:
    for path in TARGETS:
        migrate(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
