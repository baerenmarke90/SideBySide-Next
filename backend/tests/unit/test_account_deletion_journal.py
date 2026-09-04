from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from sidebyside.identity.deletion_journal import (
    DeletionJournalError,
    append_tombstone,
    initialize_journal,
    load_tombstones,
    load_tombstones_bytes,
)

INSTANCE_ID = UUID("01990000-0000-7000-8000-000000000501")
OTHER_INSTANCE_ID = UUID("01990000-0000-7000-8000-000000000502")
ACCOUNT_ID = UUID("01990000-0000-7000-8000-000000000601")
ACCEPTED_AT = datetime(2026, 9, 4, 17, 30, tzinfo=UTC)


def test_initialize_header_only_is_instance_bound(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"

    initialize_journal(journal, instance_id=INSTANCE_ID)

    assert load_tombstones(journal, expected_instance_id=INSTANCE_ID) == ()
    assert len(journal.read_text(encoding="utf-8").splitlines()) == 1
    assert journal.stat().st_mode & 0o777 == 0o600
    with pytest.raises(DeletionJournalError, match="different instance"):
        load_tombstones(journal, expected_instance_id=OTHER_INSTANCE_ID)


def test_append_and_load_round_trip(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"

    appended = append_tombstone(
        journal,
        instance_id=INSTANCE_ID,
        account_id=ACCOUNT_ID,
        accepted_at=ACCEPTED_AT,
    )
    loaded = load_tombstones(journal, expected_instance_id=INSTANCE_ID)
    snapshot = load_tombstones_bytes(
        journal.read_bytes(),
        expected_instance_id=INSTANCE_ID,
    )

    assert loaded == (appended,)
    assert snapshot == loaded
    assert len(journal.read_text(encoding="utf-8").splitlines()) == 2
    assert journal.stat().st_mode & 0o777 == 0o600


def test_same_tombstone_append_is_idempotent(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"

    first = append_tombstone(
        journal,
        instance_id=INSTANCE_ID,
        account_id=ACCOUNT_ID,
        accepted_at=ACCEPTED_AT,
    )
    second = append_tombstone(
        journal,
        instance_id=INSTANCE_ID,
        account_id=ACCOUNT_ID,
        accepted_at=ACCEPTED_AT,
    )

    assert first == second
    assert len(journal.read_text(encoding="utf-8").splitlines()) == 2


def test_same_account_with_different_acceptance_time_is_rejected(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"
    append_tombstone(
        journal,
        instance_id=INSTANCE_ID,
        account_id=ACCOUNT_ID,
        accepted_at=ACCEPTED_AT,
    )

    with pytest.raises(DeletionJournalError, match="different acceptance timestamp"):
        append_tombstone(
            journal,
            instance_id=INSTANCE_ID,
            account_id=ACCOUNT_ID,
            accepted_at=ACCEPTED_AT + timedelta(seconds=1),
        )


def test_wrong_instance_is_rejected(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"
    append_tombstone(
        journal,
        instance_id=INSTANCE_ID,
        account_id=ACCOUNT_ID,
        accepted_at=ACCEPTED_AT,
    )

    with pytest.raises(DeletionJournalError, match="different instance"):
        load_tombstones(journal, expected_instance_id=OTHER_INSTANCE_ID)


def test_empty_journal_is_rejected_even_with_expected_instance(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"
    journal.write_bytes(b"")

    with pytest.raises(DeletionJournalError, match="missing its instance header"):
        load_tombstones(journal, expected_instance_id=INSTANCE_ID)


def test_modified_header_fails_integrity_check(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"
    initialize_journal(journal, instance_id=INSTANCE_ID)
    header = json.loads(journal.read_text(encoding="utf-8"))
    header["instanceId"] = str(OTHER_INSTANCE_ID)
    journal.write_text(json.dumps(header) + "\n", encoding="utf-8")

    with pytest.raises(DeletionJournalError, match="header failed its integrity check"):
        load_tombstones(journal, expected_instance_id=INSTANCE_ID)


def test_modified_tombstone_fails_integrity_check(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"
    append_tombstone(
        journal,
        instance_id=INSTANCE_ID,
        account_id=ACCOUNT_ID,
        accepted_at=ACCEPTED_AT,
    )
    lines = journal.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[1])
    record["acceptedAt"] = "2026-09-04T18:30:00Z"
    journal.write_text(lines[0] + "\n" + json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(DeletionJournalError, match="integrity check"):
        load_tombstones(journal, expected_instance_id=INSTANCE_ID)


def test_unexpected_fields_are_rejected(tmp_path: Path) -> None:
    journal = tmp_path / "deletions.jsonl"
    append_tombstone(
        journal,
        instance_id=INSTANCE_ID,
        account_id=ACCOUNT_ID,
        accepted_at=ACCEPTED_AT,
    )
    lines = journal.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[1])
    record["email"] = "must-not-be-stored@example.invalid"
    journal.write_text(lines[0] + "\n" + json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(DeletionJournalError, match="invalid field set"):
        load_tombstones(journal, expected_instance_id=INSTANCE_ID)


def test_invalid_utf8_snapshot_is_rejected() -> None:
    with pytest.raises(DeletionJournalError, match="not valid UTF-8"):
        load_tombstones_bytes(b"\xff\xfe", expected_instance_id=INSTANCE_ID)


def test_naive_acceptance_timestamp_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DeletionJournalError, match="timezone-aware"):
        append_tombstone(
            tmp_path / "deletions.jsonl",
            instance_id=INSTANCE_ID,
            account_id=ACCOUNT_ID,
            accepted_at=datetime(2026, 9, 4, 17, 30),
        )
