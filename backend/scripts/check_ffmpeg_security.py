"""Fail-closed Debian Security Tracker gate for the pinned ffmpeg package."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

TRACKER_URL = "https://security-tracker.debian.org/tracker/data/json"
PACKAGE = "ffmpeg"
RELEASE = "trixie"
MAX_TRACKER_BYTES = 64 * 1024 * 1024
VALID_STATES = {"resolved", "open", "undetermined"}


@dataclass(frozen=True)
class AuditReport:
    accepted: tuple[str, ...]
    failures: tuple[str, ...]
    repository_versions: tuple[str, ...]


def _debian_version_is_newer(candidate: str, expected: str) -> bool:
    """Use dpkg's native ordering, including Debian epochs and revisions."""
    result = subprocess.run(
        ["dpkg", "--compare-versions", candidate, "gt", expected],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise RuntimeError("dpkg could not compare Debian package versions")


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Security Tracker schema mismatch at {label}")
    return value


def audit_tracker(
    document: Mapping[str, Any],
    expected_version: str,
    *,
    version_is_newer: Callable[[str, str], bool] = _debian_version_is_newer,
) -> AuditReport:
    """Evaluate the ffmpeg/trixie slice without making a network request."""
    package = _mapping(document.get(PACKAGE), PACKAGE)
    accepted: list[str] = []
    failures: list[str] = []
    versions: set[str] = set()

    for issue_name, raw_issue in package.items():
        if not isinstance(issue_name, str):
            raise ValueError("Security Tracker issue name is not a string")
        issue = _mapping(raw_issue, f"{PACKAGE}.{issue_name}")
        releases = _mapping(issue.get("releases"), f"{PACKAGE}.{issue_name}.releases")
        raw_release = releases.get(RELEASE)
        if raw_release is None:
            continue
        release = _mapping(raw_release, f"{PACKAGE}.{issue_name}.releases.{RELEASE}")

        status = release.get("status")
        if not isinstance(status, str) or status not in VALID_STATES:
            raise ValueError(f"Unknown Security Tracker status for {issue_name}")

        repositories = _mapping(
            release.get("repositories"),
            f"{PACKAGE}.{issue_name}.releases.{RELEASE}.repositories",
        )
        if not repositories:
            raise ValueError(f"No repository versions for {issue_name}/{RELEASE}")
        for repository, raw_version in repositories.items():
            if not isinstance(repository, str) or not repository.startswith(RELEASE):
                raise ValueError(f"Unexpected repository name for {issue_name}/{RELEASE}")
            if not isinstance(raw_version, str) or not raw_version:
                raise ValueError(f"Invalid repository version for {issue_name}/{repository}")
            versions.add(raw_version)
            if version_is_newer(raw_version, expected_version):
                failures.append(
                    f"{issue_name}: {repository} has newer ffmpeg {raw_version} "
                    f"than pin {expected_version}"
                )

        if status == "resolved":
            continue
        if status == "undetermined":
            failures.append(f"{issue_name}: trixie status is undetermined")
            continue

        urgency = release.get("urgency")
        nodsa_reason = release.get("nodsa_reason")
        if urgency == "unimportant":
            accepted.append(f"{issue_name}: open, Debian urgency=unimportant")
        elif nodsa_reason == "postponed":
            accepted.append(f"{issue_name}: open, Debian nodsa_reason=postponed")
        else:
            failures.append(
                f"{issue_name}: open for trixie without postponed/unimportant classification"
            )

    if not versions:
        raise ValueError(f"No {PACKAGE}/{RELEASE} repository versions found")
    if expected_version not in versions:
        failures.append(
            f"Pinned ffmpeg {expected_version} is not present in current {RELEASE} tracker data"
        )

    return AuditReport(
        accepted=tuple(sorted(accepted)),
        failures=tuple(sorted(set(failures))),
        repository_versions=tuple(sorted(versions)),
    )


def fetch_tracker() -> Mapping[str, Any]:
    request = urllib.request.Request(
        TRACKER_URL,
        headers={"User-Agent": "SideBySide-Next-CI/ffmpeg-security-gate"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read(MAX_TRACKER_BYTES + 1)
    except OSError as error:
        raise RuntimeError("Debian Security Tracker request failed") from error
    if len(payload) > MAX_TRACKER_BYTES:
        raise RuntimeError("Debian Security Tracker response exceeded size limit")
    try:
        parsed = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError("Debian Security Tracker returned invalid JSON") from error
    return _mapping(parsed, "root")


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("usage: check_ffmpeg_security.py <debian-ffmpeg-version>", file=sys.stderr)
        return 2

    expected_version = sys.argv[1].strip()
    try:
        report = audit_tracker(fetch_tracker(), expected_version)
    except (RuntimeError, ValueError) as error:
        print(f"ffmpeg security gate: FAIL: {error}", file=sys.stderr)
        return 1

    print(f"ffmpeg pin: {expected_version}")
    print("tracker repository versions: " + ", ".join(report.repository_versions))
    for finding in report.accepted:
        print(f"ACCEPTED DEBIAN CLASSIFICATION: {finding}")
    if report.failures:
        for finding in report.failures:
            print(f"FAIL: {finding}", file=sys.stderr)
        return 1
    print("ffmpeg security gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
