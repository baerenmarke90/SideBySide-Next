#!/usr/bin/env python3
"""Build local Self-Hosted application images without creating a second Compose manifest.

Released Self-Hosted never uses this helper. Development, CI and verified-source
acceptance may build backend/Web from a checkout or explicit remote Git contexts,
then point canonical ``compose.yaml`` at the resulting local tags with
``SBS_SELF_HOSTED_PULL_POLICY=never``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LOCAL_TAG_COMPONENT_RE = re.compile(r"^[a-z0-9_][a-z0-9_.-]{0,127}$")


class SourceBuildError(RuntimeError):
    """The requested source image build is unsafe or invalid."""


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def effective(values: dict[str, str], key: str, default: str = "") -> str:
    if key in os.environ:
        return os.environ[key]
    return values.get(key, default)


def reject_production_source_build(values: dict[str, str]) -> None:
    """Reject Production declared by either dotenv or process environment.

    A one-command process override must not be able to mask a Production dotenv
    while local source images are built for a later Compose invocation.
    """

    dotenv_environment = values.get("SBS_ENVIRONMENT", "").strip().lower()
    process_environment = os.environ.get("SBS_ENVIRONMENT", "").strip().lower()
    if dotenv_environment == "production" or process_environment == "production":
        raise SourceBuildError(
            "source builds are not allowed when SBS_ENVIRONMENT=production is declared"
        )


def require_local_tag(reference: str, label: str, repository: str) -> str:
    """Accept only an unqualified SideBySide-local repository and explicit tag.

    This is intentionally an allowlist rather than a blacklist for registry URLs.
    Source-build output must never target a registry/digest identity or a different
    repository name; publication is owned exclusively by the protected release job.
    """

    prefix = f"{repository}:"
    if not reference.startswith(prefix):
        raise SourceBuildError(f"{label} must use local repository {repository}")
    tag = reference[len(prefix) :]
    if not LOCAL_TAG_COMPONENT_RE.fullmatch(tag):
        raise SourceBuildError(f"{label} must contain a safe explicit local tag")
    return reference


def require_safe_source_context(context: str, label: str) -> str:
    """Reject URL credentials/query data before plans can reach logs or Docker.

    Remote Git authentication belongs to BuildKit/Arcane credential mechanisms,
    never inside a source URL. Query-bearing URLs are rejected as well because a
    diagnostic ``--print-plan`` would otherwise echo arbitrary query values.
    Existing supported examples use fragments (``#ref:subdir``), which remain safe.
    """

    if "://" not in context:
        return context
    try:
        parsed = urlsplit(context)
    except ValueError as exc:
        raise SourceBuildError(f"{label} is not a valid source URL") from exc
    if parsed.username is not None or parsed.password is not None:
        raise SourceBuildError(f"{label} must not contain URL credentials")
    if parsed.query:
        raise SourceBuildError(f"{label} must not contain URL query values")
    return context


def plan(
    env_file: Path,
    *,
    backend_context: str | None = None,
    web_context: str | None = None,
    revision: str | None = None,
    backend_image: str | None = None,
    web_image: str | None = None,
) -> dict[str, object]:
    values = read_dotenv(env_file)
    reject_production_source_build(values)

    resolved_revision = revision or effective(
        values, "SBS_BUILD_REVISION", "unverified-local-checkout"
    )
    resolved_backend_context = require_safe_source_context(
        backend_context
        or effective(values, "SBS_BACKEND_BUILD_CONTEXT", str(ROOT / "backend")),
        "SBS_BACKEND_BUILD_CONTEXT",
    )
    resolved_web_context = require_safe_source_context(
        web_context or effective(values, "SBS_WEB_BUILD_CONTEXT", str(ROOT / "web")),
        "SBS_WEB_BUILD_CONTEXT",
    )
    resolved_backend_image = require_local_tag(
        backend_image
        or effective(
            values,
            "SBS_SELF_HOSTED_BACKEND_IMAGE",
            "sidebyside-backend:source-local",
        ),
        "SBS_SELF_HOSTED_BACKEND_IMAGE",
        "sidebyside-backend",
    )
    resolved_web_image = require_local_tag(
        web_image
        or effective(
            values,
            "SBS_SELF_HOSTED_WEB_IMAGE",
            "sidebyside-web:source-local",
        ),
        "SBS_SELF_HOSTED_WEB_IMAGE",
        "sidebyside-web",
    )
    return {
        "revision": resolved_revision,
        "backendContext": resolved_backend_context,
        "webContext": resolved_web_context,
        "backendImage": resolved_backend_image,
        "webImage": resolved_web_image,
        "webBuildArgs": {
            "VITE_SBS_API_BASE_URL": "",
            "VITE_SBS_DEMO_MODE": effective(values, "SBS_DEMO_MODE", "false"),
            "VITE_SBS_DEMO_URL": effective(values, "SBS_DEMO_PUBLIC_URL", ""),
            "VITE_SBS_DEMO_RESET_TIMER": effective(
                values, "SBS_DEMO_MODE_RESET_TIMER", "false"
            ),
            "VITE_SBS_DEMO_RESET_INTERVAL": effective(
                values, "SBS_DEMO_MODE_RESET_INTERVAL", "6h"
            ),
        },
    }


def run_build(build_plan: dict[str, object]) -> None:
    revision = str(build_plan["revision"])
    backend = [
        "docker",
        "build",
        "--build-arg",
        f"SBS_BUILD_REVISION={revision}",
        "--tag",
        str(build_plan["backendImage"]),
        str(build_plan["backendContext"]),
    ]
    web = ["docker", "build", "--build-arg", f"SBS_BUILD_REVISION={revision}"]
    for key, value in dict(build_plan["webBuildArgs"]).items():
        web.extend(["--build-arg", f"{key}={value}"])
    web.extend(
        ["--tag", str(build_plan["webImage"]), str(build_plan["webContext"])]
    )
    try:
        subprocess.run(backend, cwd=ROOT, check=True)
        subprocess.run(web, cwd=ROOT, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SourceBuildError("Docker source image build failed") from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--backend-context")
    parser.add_argument("--web-context")
    parser.add_argument("--revision")
    parser.add_argument("--backend-image")
    parser.add_argument("--web-image")
    parser.add_argument("--print-plan", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        build_plan = plan(
            args.env_file,
            backend_context=args.backend_context,
            web_context=args.web_context,
            revision=args.revision,
            backend_image=args.backend_image,
            web_image=args.web_image,
        )
        if args.print_plan:
            print(json.dumps(build_plan, sort_keys=True))
            return 0
        run_build(build_plan)
    except (OSError, SourceBuildError) as exc:
        print(f"Self-Hosted source build refused: {exc}", file=sys.stderr)
        return 2
    print(
        "Built local Self-Hosted backend/Web images; canonical compose.yaml remains the only runtime manifest."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
