"""Policy tests for the Debian ffmpeg security gate."""

from __future__ import annotations

import pytest

from scripts.check_ffmpeg_security import audit_tracker

PIN = "7:7.1.5-0+deb13u1"


def _document(
    *,
    status: str = "resolved",
    version: str = PIN,
    urgency: str | None = None,
    nodsa_reason: str | None = None,
) -> dict[str, object]:
    release: dict[str, object] = {
        "status": status,
        "repositories": {"trixie": version, "trixie-security": version},
    }
    if urgency is not None:
        release["urgency"] = urgency
    if nodsa_reason is not None:
        release["nodsa_reason"] = nodsa_reason
    return {
        "ffmpeg": {
            "CVE-TEST": {
                "releases": {
                    "trixie": release,
                }
            }
        }
    }


def _newer(candidate: str, expected: str) -> bool:
    order = {
        "7:7.1.5-0+deb13u1": 1,
        "7:7.1.5-0+deb13u2": 2,
    }
    return order[candidate] > order[expected]


def test_resolved_current_pin_passes() -> None:
    report = audit_tracker(_document(), PIN, version_is_newer=_newer)
    assert report.failures == ()
    assert report.accepted == ()


@pytest.mark.parametrize(
    ("urgency", "reason"),
    [("unimportant", None), ("medium", "postponed")],
)
def test_debian_postponed_and_unimportant_are_visible_but_accepted(
    urgency: str,
    reason: str | None,
) -> None:
    report = audit_tracker(
        _document(status="open", urgency=urgency, nodsa_reason=reason),
        PIN,
        version_is_newer=_newer,
    )
    assert report.failures == ()
    assert len(report.accepted) == 1


def test_unclassified_open_issue_fails() -> None:
    report = audit_tracker(
        _document(status="open", urgency="medium"),
        PIN,
        version_is_newer=_newer,
    )
    assert report.failures
    assert "without postponed/unimportant" in report.failures[0]


def test_undetermined_issue_fails_closed() -> None:
    report = audit_tracker(
        _document(status="undetermined"),
        PIN,
        version_is_newer=_newer,
    )
    assert report.failures == ("CVE-TEST: trixie status is undetermined",)


def test_newer_repository_version_fails_and_exposes_pin_drift() -> None:
    report = audit_tracker(
        _document(version="7:7.1.5-0+deb13u2"),
        PIN,
        version_is_newer=_newer,
    )
    assert any("newer ffmpeg" in failure for failure in report.failures)
    assert any("not present" in failure for failure in report.failures)


def test_unknown_tracker_state_is_schema_failure() -> None:
    with pytest.raises(ValueError, match="Unknown Security Tracker status"):
        audit_tracker(
            _document(status="something-new"),
            PIN,
            version_is_newer=_newer,
        )
