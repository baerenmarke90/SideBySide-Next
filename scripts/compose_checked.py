#!/usr/bin/env python3
"""Run the canonical Compose stack with a revision derived from a clean checkout.

Direct ``docker compose`` remains the convenient local/test path and deliberately
reports ``unverified-local-checkout``. Release-candidate and Production
complete-checkout deployments use this wrapper so the revision embedded in the
backend and Web images is derived from the checked-out source rather than from an
operator-supplied environment value.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
REVISION_SERVICES = ("migrate", "demo-init", "api", "worker", "web")


class CheckoutError(RuntimeError):
    """The checkout cannot be used as a verified deployment source."""


def run_git(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CheckoutError(f"Git command failed: {' '.join(args)}") from exc
    return completed.stdout.strip()


def repository_root() -> Path:
    script_root = Path(__file__).resolve().parents[1]
    reported = Path(run_git(script_root, "rev-parse", "--show-toplevel")).resolve()
    if reported != script_root:
        raise CheckoutError("compose_checked.py must run from its own SideBySide checkout")
    return script_root


def verified_revision(root: Path, expected: str | None) -> str:
    status = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        # Do not print file names. A path in a developer checkout can itself
        # contain sensitive or user-specific information.
        raise CheckoutError("the repository is not clean; refusing a verified deployment")

    revision = run_git(root, "rev-parse", "HEAD")
    if not REVISION_RE.fullmatch(revision):
        raise CheckoutError("HEAD did not resolve to an exact 40-character Git commit SHA")

    if expected is not None:
        normalized = expected.strip().lower()
        if not REVISION_RE.fullmatch(normalized):
            raise CheckoutError("--expected-revision must be an exact 40-character commit SHA")
        if normalized != revision:
            raise CheckoutError("checked-out HEAD does not match --expected-revision")

    return revision


def revision_override(revision: str) -> dict[str, object]:
    return {
        "services": {
            service: {"build": {"args": {"SBS_BUILD_REVISION": revision}}}
            for service in REVISION_SERVICES
        }
    }


def reject_compose_file_overrides(arguments: list[str]) -> None:
    for index, argument in enumerate(arguments):
        if argument in {"-f", "--file"} or argument.startswith("--file="):
            raise CheckoutError("alternate Compose files are not allowed by the verified wrapper")
        if argument.startswith("-f") and argument != "-f":
            raise CheckoutError("alternate Compose files are not allowed by the verified wrapper")
        if argument == "--project-directory" or argument.startswith("--project-directory="):
            raise CheckoutError("--project-directory is not allowed by the verified wrapper")
        if argument == "--project-directory" and index + 1 < len(arguments):
            raise CheckoutError("--project-directory is not allowed by the verified wrapper")


def invoke_compose(root: Path, revision: str, compose_args: list[str]) -> int:
    if not compose_args:
        raise CheckoutError("a Docker Compose command is required")
    reject_compose_file_overrides(compose_args)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="sidebyside-revision-",
        delete=False,
    ) as handle:
        json.dump(revision_override(revision), handle)
        override_path = Path(handle.name)

    try:
        completed = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(root / "compose.yaml"),
                "-f",
                str(override_path),
                *compose_args,
            ],
            cwd=root,
            check=False,
        )
        return completed.returncode
    except OSError as exc:
        raise CheckoutError("docker compose could not be executed") from exc
    finally:
        override_path.unlink(missing_ok=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected-revision",
        help="Require clean HEAD to equal this exact 40-character commit SHA",
    )
    parser.add_argument(
        "--print-revision",
        action="store_true",
        help="Print the verified checkout revision without invoking Compose",
    )
    parser.add_argument("compose_args", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        root = repository_root()
        revision = verified_revision(root, args.expected_revision)
        if args.print_revision:
            if args.compose_args:
                raise CheckoutError("--print-revision cannot be combined with Compose arguments")
            print(revision)
            return 0
        return invoke_compose(root, revision, args.compose_args)
    except CheckoutError as exc:
        print(f"verified Compose deployment refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
