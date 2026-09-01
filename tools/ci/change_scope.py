#!/usr/bin/env python3
"""Classify changed paths for expensive pull-request gates.

Pull requests should only pay for checks that can be affected by their diff.
The classifier stays fail-closed for unknown paths and CI infrastructure so a
new repository surface cannot silently bypass an expensive safety gate.
Pushes to ``main`` are handled separately by the workflows and still run the
full integration suite.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

SCOPES = (
    "backend",
    "backend_integration",
    "self_hosted",
    "api_clients",
    "supply_chain",
    "deployment_guard",
    "recovery",
)

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
    ".gitignore",
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

        # The classifier and its owning workflow define the safety boundary.
        # Changes to either must exercise every gate.
        if path.startswith("tools/ci/") or path == ".github/workflows/ci.yml":
            return _all_enabled()

        known = False

        # Backend lint, typing, unit tests and the OpenAPI contract only depend
        # on backend files. Web/Android changes no longer wake this job up.
        if path.startswith("backend/"):
            result["backend"] = True
            known = True

        # PostgreSQL/Alembic integration is relevant for runtime backend code,
        # migrations, integration fixtures/tests and Python dependency changes.
        if _matches(
            path,
            prefixes=(
                "backend/src/",
                "backend/alembic/",
                "backend/tests/integration/",
            ),
            exact=(
                "backend/alembic.ini",
                "backend/tests/conftest.py",
                "backend/pyproject.toml",
                "backend/uv.lock",
            ),
        ):
            result["backend_integration"] = True
            known = True

        # The documented self-hosted stack is sensitive to container/runtime
        # wiring, not ordinary application UI source.
        if _matches(
            path,
            prefixes=("web/docker-entrypoint.d/",),
            exact=(
                ".env.example",
                *SELF_HOSTED_COMPOSE_FILES,
                "backend/Dockerfile",
                "web/Dockerfile",
                "web/nginx.conf",
                "backend/src/sidebyside/config.py",
                "backend/src/sidebyside/main.py",
                "docs/SELF-HOSTING.md",
                "docs/ARCANE.md",
            ),
        ):
            result["self_hosted"] = True
            known = True

        # Generated Web/Android clients only need regeneration when their
        # OpenAPI input or generator surfaces change.
        if _matches(
            path,
            prefixes=(
                "tools/openapi/",
                "web/src/api/generated/",
                "android/api/generated/",
            ),
            exact=(
                "backend/openapi.json",
                "backend/scripts/openapi_contract.py",
            ),
        ):
            result["api_clients"] = True
            known = True

        # Supply-chain work is dependency/build related; normal backend source
        # changes do not need a fresh audit and two no-cache container builds.
        if _matches(
            path,
            exact=(
                "backend/pyproject.toml",
                "backend/uv.lock",
                "backend/Dockerfile",
                "web/Dockerfile",
                "docs/DEPENDENCIES.md",
                ".github/dependabot.yml",
            ),
        ):
            result["supply_chain"] = True
            known = True

        # Network/port/CSP checks are tied to deployment and proxy surfaces.
        if _matches(
            path,
            prefixes=("web/docker-entrypoint.d/",),
            exact=(
                ".github/workflows/self-hosted-deployment-guard.yml",
                ".env.example",
                *SELF_HOSTED_COMPOSE_FILES,
                "backend/Dockerfile",
                "web/Dockerfile",
                "web/nginx.conf",
                "web/scripts/check_csp_header.sh",
                "backend/src/sidebyside/config.py",
                "backend/src/sidebyside/main.py",
                "docs/SELF-HOSTING.md",
                "docs/ARCANE.md",
            ),
        ):
            result["deployment_guard"] = True
            known = True

        # Recovery acceptance is expensive and is needed for actual recovery
        # tooling/contracts plus schema migrations that an old snapshot must
        # survive. Ordinary backend or Web feature work does not affect it.
        if _matches(
            path,
            prefixes=("backend/alembic/",),
            exact=(
                ".github/workflows/self-hosted-recovery.yml",
                ".env.example",
                *SELF_HOSTED_COMPOSE_FILES,
                "scripts/self_hosted_recovery.py",
                "scripts/self_hosted_recovery_acceptance.py",
                "scripts/test_self_hosted_recovery.py",
                "docs/SELF-HOSTED-RECOVERY.md",
                "docs/SELF-HOSTING.md",
                "docs/DEVELOPMENT-AND-RELEASE-ENVIRONMENTS.md",
                "docs/ARCANE.md",
            ),
        ):
            result["recovery"] = True
            known = True

        # Ordinary client source is intentionally known but does not activate
        # backend/container gates. Client-specific workflows cover these trees.
        if path.startswith(("web/", "android/")):
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
