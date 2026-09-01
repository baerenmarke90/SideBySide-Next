#!/usr/bin/env python3
"""Run canonical Compose from an immutable snapshot of a clean Git checkout.

Direct ``docker compose`` remains the convenient local/test path and deliberately
reports ``unverified-local-checkout``. Release-candidate and Production
complete-checkout deployments use this wrapper. It derives the revision from Git
and exports the backend/Web build contexts from that committed tree, so ignored or
untracked local files cannot enter a verified image.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
BACKEND_SERVICES = ("migrate", "demo-init", "api", "worker")


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


def export_build_snapshot(root: Path, revision: str, target: Path) -> None:
    """Export only committed backend/Web files without trusting the worktree."""
    archive_path = target / "source.tar"
    try:
        with archive_path.open("wb") as archive_file:
            subprocess.run(
                ["git", "archive", "--format=tar", revision, "backend", "web"],
                cwd=root,
                check=True,
                stdout=archive_file,
                stderr=subprocess.PIPE,
            )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CheckoutError("Git could not export the verified source tree") from exc

    target_root = target.resolve()
    try:
        with tarfile.open(archive_path, mode="r:") as archive:
            for member in archive.getmembers():
                destination = (target / member.name).resolve()
                if destination != target_root and target_root not in destination.parents:
                    raise CheckoutError("Git archive contained an invalid path")
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    raise CheckoutError("verified build source contains an unsupported link/device")
                source = archive.extractfile(member)
                if source is None:
                    raise CheckoutError("Git archive member could not be read")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with source, destination.open("wb") as output:
                    output.write(source.read())
                os.chmod(destination, member.mode & 0o777)
    except (OSError, tarfile.TarError) as exc:
        raise CheckoutError("verified Git source snapshot could not be extracted") from exc
    finally:
        archive_path.unlink(missing_ok=True)


def compose_override(revision: str, snapshot_root: Path) -> dict[str, object]:
    backend_build = {
        "context": str(snapshot_root / "backend"),
        "args": {"SBS_BUILD_REVISION": revision},
    }
    services: dict[str, object] = {
        service: {"build": backend_build} for service in BACKEND_SERVICES
    }
    services["web"] = {
        "build": {
            "context": str(snapshot_root / "web"),
            "args": {"SBS_BUILD_REVISION": revision},
        }
    }
    return {"services": services}


def reject_compose_source_overrides(arguments: list[str]) -> None:
    for argument in arguments:
        if argument in {"-f", "--file"} or argument.startswith("--file="):
            raise CheckoutError("alternate Compose files are not allowed by the verified wrapper")
        if argument.startswith("-f") and argument != "-f":
            raise CheckoutError("alternate Compose files are not allowed by the verified wrapper")
        if argument == "--project-directory" or argument.startswith("--project-directory="):
            raise CheckoutError("--project-directory is not allowed by the verified wrapper")


def invoke_compose(root: Path, revision: str, compose_args: list[str]) -> int:
    if not compose_args:
        raise CheckoutError("a Docker Compose command is required")
    reject_compose_source_overrides(compose_args)

    try:
        with tempfile.TemporaryDirectory(prefix="sidebyside-source-") as temp_dir:
            snapshot_root = Path(temp_dir)
            export_build_snapshot(root, revision, snapshot_root)
            override_path = snapshot_root / "compose.revision.json"
            override_path.write_text(
                json.dumps(compose_override(revision, snapshot_root)),
                encoding="utf-8",
            )
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
