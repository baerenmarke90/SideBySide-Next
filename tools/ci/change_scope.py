#!/usr/bin/env python3
"""Conservatively classify paths for expensive pull-request gates.

Ordinary documentation must not start runtime, PostgreSQL, or container gates.
As soon as a relevant or unknown file is affected, enable the corresponding
gates, or all expensive gates fail-closed when the effect is unknown. Workflow
pushes to main always run every expensive gate separately.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

SCOPES = ("backend", "self_hosted", "supply_chain", "deployment_guard")

SAFE_DOC_PREFIXES = ("docs/", "specification/")
SAFE_DOC_EXACT = (
    "README.md",
    "AGENTS.md",
    "CLA.md",
    "COMMERCIAL-LICENSE.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "PROVENANCE.md",
    "TRADEMARKS.md",
    ".gitleaksignore",
)
SELF_HOSTED_COMPOSE_FILES = ("compose.yaml", "compose.arcane.yaml")


def _matches(path: str, *, prefixes: tuple[str, ...] = (), exact: tuple[str, ...] = ()) -> bool:
    return path in exact or any(path.startswith(prefix) for prefix in prefixes)


def _all_enabled() -> dict[str, bool]:
    return {scope: True for scope in SCOPES}


def _is_explicitly_safe_documentation(path: str) -> bool:
    return path in SAFE_DOC_EXACT or any(path.startswith(prefix) for prefix in SAFE_DOC_PREFIXES)


def classify_paths(paths: Iterable[str]) -> dict[str, bool]:
    result = {scope: False for scope in SCOPES}

    for raw_path in paths:
        path = raw_path.strip().replace("\\", "/")
        if not path:
            continue

        if path.startswith("tools/ci/"):
            return _all_enabled()

        known = False

        if _matches(
            path,
            prefixes=("backend/", "web/", "android/"),
            exact=(
                ".github/workflows/ci.yml",
                ".env.example",
                *SELF_HOSTED_COMPOSE_FILES,
                ".gitignore",
            ),
        ):
            result["backend"] = True
            known = True

        if _matches(
            path,
            prefixes=("backend/", "web/"),
            exact=(
                ".github/workflows/ci.yml",
                ".env.example",
                *SELF_HOSTED_COMPOSE_FILES,
                "docs/SELF-HOSTING.md",
                "docs/ARCANE.md",
            ),
        ):
            result["self_hosted"] = True
            known = True

        if _matches(
            path,
            prefixes=("backend/",),
            exact=(
                ".github/workflows/ci.yml",
                "docs/DEPENDENCIES.md",
                "web/Dockerfile",
            ),
        ):
            result["supply_chain"] = True
            known = True

        if _matches(
            path,
            prefixes=("backend/", "web/"),
            exact=(
                ".github/workflows/self-hosted-deployment-guard.yml",
                ".env.example",
                *SELF_HOSTED_COMPOSE_FILES,
                "docs/SELF-HOSTING.md",
                "docs/ARCANE.md",
            ),
        ):
            result["deployment_guard"] = True
            known = True

        if _is_explicitly_safe_documentation(path):
            known = True

        if not known:
            return _all_enabled()

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("changed_files", type=Path, help="File with one changed path per line")
    args = parser.parse_args()

    paths = args.changed_files.read_text(encoding="utf-8").splitlines()
    for scope, enabled in classify_paths(paths).items():
        print(f"{scope}={'true' if enabled else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
