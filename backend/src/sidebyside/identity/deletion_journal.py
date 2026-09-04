"""Forward-only Account-deletion tombstones outside point-in-time database backups."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any, TextIO
from uuid import UUID

JOURNAL_FORMAT = "sidebyside-account-deletion-journal"
JOURNAL_VERSION = 1
_HEADER_RECORD_TYPE = "INSTANCE"
_TOMBSTONE_RECORD_TYPE = "ACCOUNT_DELETION"
_HEADER_KEYS = frozenset(
    {
        "format",
        "formatVersion",
        "recordType",
        "instanceId",
        "sha256",
    }
)
_TOMBSTONE_KEYS = frozenset(
    {
        "format",
        "formatVersion",
        "recordType",
        "instanceId",
        "accountId",
        "acceptedAt",
        "sha256",
    }
)


class DeletionJournalError(RuntimeError):
    """The deletion journal is missing, inconsistent, or corrupted."""


@dataclass(frozen=True)
class DeletionTombstone:
    """Minimal restore authority for one irreversibly accepted Account deletion."""

    instance_id: UUID
    account_id: UUID
    accepted_at: datetime
    sha256: str


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DeletionJournalError("Deletion acceptance timestamp must be timezone-aware.")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _header_payload(instance_id: UUID) -> dict[str, Any]:
    return {
        "format": JOURNAL_FORMAT,
        "formatVersion": JOURNAL_VERSION,
        "recordType": _HEADER_RECORD_TYPE,
        "instanceId": str(instance_id),
    }


def _tombstone_payload(
    *,
    instance_id: UUID,
    account_id: UUID,
    accepted_at: datetime,
) -> dict[str, Any]:
    return {
        "format": JOURNAL_FORMAT,
        "formatVersion": JOURNAL_VERSION,
        "recordType": _TOMBSTONE_RECORD_TYPE,
        "instanceId": str(instance_id),
        "accountId": str(account_id),
        "acceptedAt": _timestamp(accepted_at),
    }


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _line(payload: dict[str, Any]) -> str:
    return json.dumps(
        {**payload, "sha256": _digest(payload)},
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def _json_record(raw: str, *, line_number: int) -> dict[str, Any]:
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DeletionJournalError(
            f"Deletion journal line {line_number} is not valid JSON."
        ) from exc
    if not isinstance(record, dict):
        raise DeletionJournalError(f"Deletion journal line {line_number} is not an object.")
    return record


def _record_digest_is_valid(record: dict[str, Any], payload: dict[str, Any]) -> bool:
    actual_digest = record.get("sha256")
    return isinstance(actual_digest, str) and actual_digest == _digest(payload)


def _parse_header(raw: str, *, line_number: int) -> UUID:
    record = _json_record(raw, line_number=line_number)
    if frozenset(record) != _HEADER_KEYS:
        raise DeletionJournalError("Deletion journal header has an invalid field set.")
    if (
        record.get("format") != JOURNAL_FORMAT
        or record.get("formatVersion") != JOURNAL_VERSION
        or record.get("recordType") != _HEADER_RECORD_TYPE
    ):
        raise DeletionJournalError("Deletion journal header uses an unsupported format.")
    try:
        instance_id = UUID(str(record["instanceId"]))
    except (ValueError, TypeError) as exc:
        raise DeletionJournalError("Deletion journal header contains an invalid instance id.") from exc
    if not _record_digest_is_valid(record, _header_payload(instance_id)):
        raise DeletionJournalError("Deletion journal header failed its integrity check.")
    return instance_id


def _parse_tombstone(raw: str, *, line_number: int) -> DeletionTombstone:
    record = _json_record(raw, line_number=line_number)
    if frozenset(record) != _TOMBSTONE_KEYS:
        raise DeletionJournalError(f"Deletion journal line {line_number} has an invalid field set.")
    if (
        record.get("format") != JOURNAL_FORMAT
        or record.get("formatVersion") != JOURNAL_VERSION
        or record.get("recordType") != _TOMBSTONE_RECORD_TYPE
    ):
        raise DeletionJournalError(
            f"Deletion journal line {line_number} uses an unsupported format."
        )
    try:
        instance_id = UUID(str(record["instanceId"]))
        account_id = UUID(str(record["accountId"]))
        accepted_at = datetime.fromisoformat(str(record["acceptedAt"]).replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise DeletionJournalError(
            f"Deletion journal line {line_number} contains an invalid identifier or timestamp."
        ) from exc
    if accepted_at.tzinfo is None or accepted_at.utcoffset() is None:
        raise DeletionJournalError(
            f"Deletion journal line {line_number} contains a naive timestamp."
        )
    accepted_at = accepted_at.astimezone(UTC)
    payload = _tombstone_payload(
        instance_id=instance_id,
        account_id=account_id,
        accepted_at=accepted_at,
    )
    actual_digest = record.get("sha256")
    if not _record_digest_is_valid(record, payload):
        raise DeletionJournalError(
            f"Deletion journal line {line_number} failed its integrity check."
        )
    assert isinstance(actual_digest, str)
    return DeletionTombstone(instance_id, account_id, accepted_at, actual_digest)


def _read_records(handle: TextIO) -> tuple[UUID, tuple[DeletionTombstone, ...]]:
    handle.seek(0)
    iterator = enumerate(handle, start=1)
    try:
        header_line_number, raw_header = next(iterator)
    except StopIteration as exc:
        raise DeletionJournalError("Deletion journal is missing its instance header.") from exc
    header = raw_header.strip()
    if not header:
        raise DeletionJournalError("Deletion journal is missing its instance header.")
    instance_id = _parse_header(header, line_number=header_line_number)

    records: list[DeletionTombstone] = []
    seen_accounts: set[UUID] = set()
    for line_number, raw in iterator:
        line = raw.strip()
        if not line:
            raise DeletionJournalError(f"Deletion journal line {line_number} is empty.")
        record = _parse_tombstone(line, line_number=line_number)
        if record.instance_id != instance_id:
            raise DeletionJournalError("Deletion journal mixes multiple instance identifiers.")
        if record.account_id in seen_accounts:
            raise DeletionJournalError("Deletion journal contains a duplicate Account tombstone.")
        seen_accounts.add(record.account_id)
        records.append(record)
    return instance_id, tuple(records)


def _validate_instance(
    journal_instance_id: UUID,
    expected_instance_id: UUID | None,
    records: tuple[DeletionTombstone, ...],
) -> tuple[DeletionTombstone, ...]:
    if expected_instance_id is not None and journal_instance_id != expected_instance_id:
        raise DeletionJournalError("Deletion journal belongs to a different instance.")
    return records


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError as exc:
        raise DeletionJournalError("Deletion journal directory could not be synchronized.") from exc
    try:
        os.fsync(descriptor)
    except OSError as exc:
        raise DeletionJournalError("Deletion journal directory could not be synchronized.") from exc
    finally:
        os.close(descriptor)


def load_tombstones_text(
    content: str,
    *,
    expected_instance_id: UUID | None = None,
) -> tuple[DeletionTombstone, ...]:
    """Validate a journal snapshot already read through a protected transport."""
    with StringIO(content) as handle:
        journal_instance_id, records = _read_records(handle)
    return _validate_instance(journal_instance_id, expected_instance_id, records)


def load_tombstones_bytes(
    content: bytes,
    *,
    expected_instance_id: UUID | None = None,
) -> tuple[DeletionTombstone, ...]:
    """Validate UTF-8 journal bytes, for example when recovery passes them on stdin."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DeletionJournalError("Deletion journal is not valid UTF-8.") from exc
    return load_tombstones_text(text, expected_instance_id=expected_instance_id)


def load_tombstones(
    path: str | Path,
    *,
    expected_instance_id: UUID | None = None,
) -> tuple[DeletionTombstone, ...]:
    """Validate and load all tombstones without exposing record contents to logs."""
    journal = Path(path)
    try:
        with journal.open("r", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            journal_instance_id, records = _read_records(handle)
    except OSError as exc:
        raise DeletionJournalError("Deletion journal could not be opened.") from exc
    return _validate_instance(journal_instance_id, expected_instance_id, records)


def initialize_journal(path: str | Path, *, instance_id: UUID) -> None:
    """Create a durable instance-bound journal even before the first deletion."""
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(journal, flags, 0o600)
    except OSError as exc:
        raise DeletionJournalError("Deletion journal could not be initialized.") from exc
    try:
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "r+", encoding="utf-8", closefd=False) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.seek(0)
                    handle.write(_line(_header_payload(instance_id)))
                else:
                    journal_instance_id, _ = _read_records(handle)
                    if journal_instance_id != instance_id:
                        raise DeletionJournalError("Deletion journal belongs to a different instance.")
                handle.flush()
                os.fsync(handle.fileno())
            _fsync_directory(journal.parent)
        except OSError as exc:
            raise DeletionJournalError("Deletion journal initialization could not be synchronized.") from exc
    finally:
        os.close(descriptor)


def append_tombstone(
    path: str | Path,
    *,
    instance_id: UUID,
    account_id: UUID,
    accepted_at: datetime,
) -> DeletionTombstone:
    """Durably append one Account tombstone, idempotent by instance and Account id."""
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    payload = _tombstone_payload(
        instance_id=instance_id,
        account_id=account_id,
        accepted_at=accepted_at,
    )
    digest = _digest(payload)
    normalized_at = datetime.fromisoformat(str(payload["acceptedAt"]).replace("Z", "+00:00"))
    candidate = DeletionTombstone(instance_id, account_id, normalized_at, digest)
    tombstone_line = _line(payload)

    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(journal, flags, 0o600)
    except OSError as exc:
        raise DeletionJournalError("Deletion journal could not be opened for append.") from exc
    try:
        try:
            result = candidate
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "r+", encoding="utf-8", closefd=False) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.seek(0)
                    handle.write(_line(_header_payload(instance_id)))
                    records: tuple[DeletionTombstone, ...] = ()
                else:
                    journal_instance_id, records = _read_records(handle)
                    if journal_instance_id != instance_id:
                        raise DeletionJournalError("Deletion journal belongs to a different instance.")
                existing = next(
                    (record for record in records if record.account_id == account_id),
                    None,
                )
                if existing is not None:
                    if existing.accepted_at != candidate.accepted_at:
                        raise DeletionJournalError(
                            "Account tombstone already exists with a different acceptance timestamp."
                        )
                    result = existing
                else:
                    handle.seek(0, os.SEEK_END)
                    handle.write(tombstone_line)
                handle.flush()
                os.fsync(handle.fileno())
            _fsync_directory(journal.parent)
        except OSError as exc:
            raise DeletionJournalError("Deletion journal append could not be synchronized.") from exc
        return result
    finally:
        os.close(descriptor)
