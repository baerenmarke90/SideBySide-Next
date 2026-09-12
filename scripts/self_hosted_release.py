#!/usr/bin/env python3
"""Operate released Self-Hosted eimir. through the fail-closed image identity gate.

This is the supported Production entry point for the released Self-Hosted bundle.
It always uses repository-root ``compose.yaml``, the ``self-hosted`` profile and an
explicit dotenv file. Image identity is validated before any pull/bootstrap/start;
normal deployment additionally requires the complete Production runtime guard.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "compose.yaml"
RUNTIME_CHECKER = ROOT / "scripts" / "check_runtime_environment.py"


class ReleaseOperationError(RuntimeError):
    """The requested released Self-Hosted operation is unsafe or invalid."""


def dotenv_value(path: Path, key: str) -> str | None:
    if not path.is_file():
        raise ReleaseOperationError(f"release env file does not exist: {path}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ReleaseOperationError("release env file could not be read") from exc
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        candidate, value = line.split("=", 1)
        if candidate.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value
    return None


def require_release_environment(env_file: Path) -> None:
    dotenv_environment = (dotenv_value(env_file, "SBS_ENVIRONMENT") or "").strip().lower()
    if dotenv_environment != "production":
        raise ReleaseOperationError(
            "released Self-Hosted requires SBS_ENVIRONMENT=production in the env file"
        )

    process_environment = os.environ.get("SBS_ENVIRONMENT")
    if process_environment is not None and process_environment.strip().lower() != "production":
        raise ReleaseOperationError(
            "process SBS_ENVIRONMENT must be unset or production for released Self-Hosted"
        )


def compose_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("COMPOSE_FILE", None)
    environment["COMPOSE_PROFILES"] = "self-hosted"
    return environment


def compose_prefix(env_file: Path) -> list[str]:
    return [
        "docker",
        "compose",
        "--profile",
        "self-hosted",
        "--env-file",
        str(env_file),
        "--file",
        str(COMPOSE_FILE),
    ]


def run_checked(command: list[str], *, action: str, environment: dict[str, str]) -> None:
    try:
        subprocess.run(command, cwd=ROOT, env=environment, check=True)
    except OSError as exc:
        raise ReleaseOperationError(f"{action} could not be executed") from exc
    except subprocess.CalledProcessError as exc:
        raise ReleaseOperationError(f"{action} failed") from exc


def validate_release(env_file: Path, *, image_identity_only: bool) -> None:
    command = [
        sys.executable,
        str(RUNTIME_CHECKER),
        "--env-file",
        str(env_file),
        "--compose-file",
        str(COMPOSE_FILE),
        "--profile",
        "self-hosted",
    ]
    if image_identity_only:
        command.append("--image-identity-only")
    run_checked(command, action="Self-Hosted release validation", environment=compose_environment())


def pull_release(env_file: Path) -> None:
    validate_release(env_file, image_identity_only=True)
    run_checked(
        [*compose_prefix(env_file), "pull"],
        action="Self-Hosted release image pull",
        environment=compose_environment(),
    )


def bootstrap_deletion_authority(env_file: Path) -> None:
    validate_release(env_file, image_identity_only=True)
    environment = compose_environment()
    run_checked(
        [*compose_prefix(env_file), "pull", "api"],
        action="Self-Hosted bootstrap image pull",
        environment=environment,
    )
    run_checked(
        [
            *compose_prefix(env_file),
            "run",
            "--rm",
            "--no-deps",
            "api",
            "python",
            "-m",
            "sidebyside.identity.deletion_bootstrap",
            "--confirm-new-installation",
        ],
        action="Self-Hosted deletion-authority bootstrap",
        environment=environment,
    )


def deploy_release(env_file: Path) -> None:
    validate_release(env_file, image_identity_only=False)
    environment = compose_environment()
    run_checked(
        [*compose_prefix(env_file), "pull"],
        action="Self-Hosted release image pull",
        environment=environment,
    )
    run_checked(
        [
            *compose_prefix(env_file),
            "up",
            "-d",
            "--force-recreate",
            "--wait",
            "--wait-timeout",
            "300",
        ],
        action="Self-Hosted release deployment",
        environment=environment,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument(
        "operation",
        choices=("validate", "pull", "bootstrap-deletion-authority", "deploy"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        require_release_environment(args.env_file)
        if args.operation == "validate":
            validate_release(args.env_file, image_identity_only=False)
        elif args.operation == "pull":
            pull_release(args.env_file)
        elif args.operation == "bootstrap-deletion-authority":
            bootstrap_deletion_authority(args.env_file)
        elif args.operation == "deploy":
            deploy_release(args.env_file)
    except ReleaseOperationError as exc:
        print(f"Self-Hosted release operation refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
