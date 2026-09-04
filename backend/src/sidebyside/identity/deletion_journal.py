"""Forward-only Account-deletion tombstones outside point-in-time database backups."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

JOURNAL_FORMAT = "sidebyside-account-deletion-journal"
JOURNAL_VERSION = 1
_RECORD_KEYS = frozenset(
    {
        "format",
        "formatVersion",
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


def _payload(*, instance_id: UUID, account_id: UUID, accepted_at: datetime) -> dict[str, Any]:
    return {
        "format": JOURNAL_FORMAT,
        "formatVersion": JOURNAL_VERSION,
        "instanceId": str(instance_id),
        "accountId": str(account_id),
        "acceptedAt": _timestamp(accepted_at),
    }


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _parse_record(raw: str, *, line_number: int) -> DeletionTombstone:
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DeletionJournalError(
            f"Deletion journal line {line_number} is not valid JSON."
        ) from exc
    if not isinstance(record, dict) or frozenset(record) != _RECORD_KEYS:
        raise DeletionJournalError(
            f"Deletion journal line {line_number} has an invalid field set."
        )
    if record.get("format") != JOURNAL_FORMAT or record.get("formatVersion") != JOURNAL_VERSION:
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
    payload = _payload(
        instance_id=instance_id,
        account_id=account_id,
        accepted_at=accepted_at,
    )
    expected_digest = _digest(payload)
    actual_digest = record.get("sha256")
    if not isinstance(actual_digest, str) or actual_digest != expected_digest:
        raise DeletionJournalError(
            f"Deletion journal line {line_number} failed its integrity check."
        )
    return DeletionTombstone(instance_id, account_id, accepted_at, actual_digest)


def _read_records(handle: Any) -> tuple[DeletionTombstone, ...]:
    handle.seek(0)
    records: list[DeletionTombstone] = []
    seen_accounts: set[UUID] = set()
    instance_id: UUID | None = None
    for line_number, raw in enumerate(handle, start=1):
        line = raw.strip()
        if not line:
            raise DeletionJournalError(
                f"Deletion journal line {line_number} is empty."
            )
        record = _parse_record(line, line_number=line_number)
        if instance_id is None:
            instance_id = record.instance_id
        elif record.instance_id != instance_id:
            raise DeletionJournalError("Deletion journal mixes multiple instance identifiers.")
        if record.account_id in seen_accounts:
            raise DeletionJournalError("Deletion journal contains a duplicate Account tombstone.")
        seen_accounts.add(record.account_id)
        records.append(record)
    return tuple(records)


def load_tombstones(
    path: str | Path,
    *,
    expected_instance_id: UUID | None = None,
) -> tuple[DeletionTombstone, ...]:
    """Validate and load all tombstones without exposing record contents to logs."""
    journal = Path(path)
    try:
        with journal.open("r", encoding="utf-8") as handle:
            records = _read_records(handle)
    except OSError as exc:
        raise DeletionJournalError("Deletion journal could not be opened.") from exc
    if expected_instance_id is not None and any(
        record.instance_id != expected_instance_id for record in records
    ):
        raise DeletionJournalError("Deletion journal belongs to a different instance.")
    return records


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
    payload = _payload(
        instance_id=instance_id,
        account_id=account_id,
        accepted_at=accepted_at,
    )
    digest = _digest(payload)
    normalized_at = datetime.fromisoformat(str(payload["acceptedAt"]).replace("Z", "+00:00"))
    candidate = DeletionTombstone(instance_id, account_id, normalized_at, digest)
    line = json.dumps({**payload, "sha256": digest}, sort_keys=True, separators=(",", ":")) + "\n"

    descriptor = os.open(journal, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "r+", encoding="utf-8", closefd=False) as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            records = _read_records(handle)
            if any(record.instance_id != instance_id for record in records):
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
                return existing
            handle.seek(0, os.SEEK_END)
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
            return candidate
    finally:
        os.close(descriptor)
