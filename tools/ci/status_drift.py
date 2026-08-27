#!/usr/bin/env python3
"""Prueft laufende Statusdokumente auf objektiv erkennbare Drift.

Historische Reviews sind absichtlich ausserhalb dieses Checks. Living-Status-Dateien
duerfen keinen angeblich "aktuellen" main-SHA konservieren, weil dieser nach dem
naechsten Merge sofort veraltet. Offene GitHub-Issues werden nur dort live
verifiziert, wo das Dokument sie explizit als offene Markdown-Task fuehrt.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

LIVING_STATUS_FILES = (
    Path("docs/IMPLEMENTATION-STATUS.md"),
    Path("docs/ROADMAP.md"),
)

CURRENT_MAIN_SHA = re.compile(
    r"(?im)^.*Aktueller\s+`?main`?\s*:\s*`?[0-9a-f]{7,40}`?.*$"
)
OPEN_ISSUE_TASK = re.compile(r"(?m)^\s*-\s*\[ \].*?#(?P<number>\d+)\b")

IssueStateFetcher = Callable[[int], str]


def validate_text(path: Path, text: str, issue_state: IssueStateFetcher | None = None) -> list[str]:
    errors: list[str] = []

    if CURRENT_MAIN_SHA.search(text):
        errors.append(
            f"{path}: Living-Status darf keinen statischen 'Aktueller main'-SHA enthalten. "
            "GitHub main ist die kanonische SHA-Quelle."
        )

    if issue_state is not None:
        for match in OPEN_ISSUE_TASK.finditer(text):
            number = int(match.group("number"))
            state = issue_state(number)
            if state != "open":
                errors.append(
                    f"{path}: Issue #{number} ist als offen markiert, GitHub meldet aber '{state}'."
                )

    return errors


def github_issue_state_fetcher(repository: str, token: str) -> IssueStateFetcher:
    cache: dict[int, str] = {}

    def fetch(number: int) -> str:
        if number in cache:
            return cache[number]

        request = urllib.request.Request(
            f"https://api.github.com/repos/{repository}/issues/{number}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "sidebyside-status-drift-guard",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"GitHub-Issue #{number} konnte nicht geprueft werden: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"GitHub-Issue #{number} konnte nicht geprueft werden: {exc.reason}") from exc

        state = payload.get("state")
        if state not in {"open", "closed"}:
            raise RuntimeError(f"GitHub-Issue #{number} liefert ungueltigen Status: {state!r}")
        cache[number] = state
        return state

    return fetch


def check_repository(root: Path, issue_state: IssueStateFetcher | None = None) -> list[str]:
    errors: list[str] = []
    for relative_path in LIVING_STATUS_FILES:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"{relative_path}: Living-Status-Datei fehlt.")
            continue
        errors.extend(validate_text(relative_path, path.read_text(encoding="utf-8"), issue_state))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--online",
        action="store_true",
        help="Explizit als offen gefuehrte Issues gegen GitHub verifizieren.",
    )
    args = parser.parse_args()

    fetcher: IssueStateFetcher | None = None
    if args.online:
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        token = os.environ.get("GITHUB_TOKEN", "")
        if not repository or not token:
            print("--online verlangt GITHUB_REPOSITORY und GITHUB_TOKEN.", file=sys.stderr)
            return 2
        fetcher = github_issue_state_fetcher(repository, token)

    try:
        errors = check_repository(args.root, fetcher)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if errors:
        print("Status-Drift erkannt:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Living-Status ist widerspruchsfrei pruefbar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
