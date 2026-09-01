#!/usr/bin/env python3
"""Fail when Development and Production environment files obviously share state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SENSITIVE_KEYS = (
    "POSTGRES_PASSWORD",
    "SBS_CURSOR_SIGNING_KEY",
    "SBS_BOOTSTRAP_TOKEN",
    "SBS_S3_ACCESS_KEY_ID",
    "SBS_S3_SECRET_ACCESS_KEY",
    "SBS_S3_SESSION_TOKEN",
    "SBS_SMTP_USERNAME",
    "SBS_SMTP_PASSWORD",
)


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"{path}:{lineno}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def nonempty_equal(left: dict[str, str], right: dict[str, str], key: str) -> bool:
    return bool(left.get(key)) and left.get(key) == right.get(key)


def check_isolation(development: dict[str, str], production: dict[str, str]) -> list[str]:
    problems: list[str] = []

    if development.get("SBS_ENVIRONMENT") != "development":
        problems.append("Development file must set SBS_ENVIRONMENT=development")
    if production.get("SBS_ENVIRONMENT") != "production":
        problems.append("Production file must set SBS_ENVIRONMENT=production")

    for key in ("COMPOSE_PROJECT_NAME", "SBS_PUBLIC_BASE_URL"):
        if not development.get(key) or not production.get(key):
            problems.append(f"Both files must set {key}")
        elif development[key] == production[key]:
            problems.append(f"Development and Production must not share {key}")

    if nonempty_equal(development, production, "SBS_DATABASE_URL"):
        problems.append("Development and Production must not share SBS_DATABASE_URL")

    for key in SENSITIVE_KEYS:
        if nonempty_equal(development, production, key):
            problems.append(f"Development and Production must not reuse {key}")

    dev_media = development.get("SBS_MEDIA_STORE", "local")
    prod_media = production.get("SBS_MEDIA_STORE", "local")
    if dev_media == "s3" and prod_media == "s3":
        if nonempty_equal(development, production, "SBS_S3_BUCKET"):
            problems.append("Development and Production must not share SBS_S3_BUCKET")

    # OIDC configuration often contains client secrets. Treat exact reuse as a
    # warning/failure without parsing or printing the JSON payload.
    if nonempty_equal(development, production, "SBS_OIDC_CONNECTIONS") and development.get(
        "SBS_OIDC_CONNECTIONS"
    ) not in {"[]", ""}:
        problems.append("Development and Production must not reuse SBS_OIDC_CONNECTIONS")

    return problems


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development", type=Path, help="Development dotenv file")
    parser.add_argument("production", type=Path, help="Production dotenv file")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit only variable names/messages as JSON; secret values are never emitted",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        development = parse_dotenv(args.development)
        production = parse_dotenv(args.production)
        problems = check_isolation(development, production)
    except (OSError, ValueError) as exc:
        print(f"environment isolation check failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}, ensure_ascii=False))
    elif problems:
        print("environment isolation check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
    else:
        print("environment isolation check passed")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
