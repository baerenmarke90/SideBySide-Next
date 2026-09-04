#!/usr/bin/env python3
"""Prove a post-backup Account deletion cannot be resurrected by restore."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from scripts.self_hosted_recovery_acceptance import (
    ATTACHMENT_ID,
    DURABLE_ORIGINAL,
    MEMORY_ID,
    OWNER_EMAIL,
    PARTNER_EMAIL,
    PARTNER_PRIVATE_HEART_ID,
    PRIVATE_HEART_ID,
    SPACE_ID,
    AcceptanceError,
    Scenario,
    available_port,
    run,
    write_environment,
)

ROOT = Path(__file__).resolve().parents[1]
RECONCILE_SCRIPT = ROOT / "scripts" / "self_hosted_deletion_reconcile.py"

INSTANCE_ID = "01990000-0000-7000-8000-000000000901"
OWNER_ID = "01990000-0000-7000-8000-000000000001"
ACCEPTED_AT = "2026-09-04T17:30:00Z"
JOURNAL_CONTAINER = "/sidebyside-journal/deletions.jsonl"


def _append_synthetic_tombstone(scenario: Scenario, journal: Path) -> None:
    journal.parent.mkdir(parents=True, exist_ok=True)
    code = (
        "from datetime import datetime; from pathlib import Path; from uuid import UUID; "
        "from sidebyside.identity.deletion_journal import append_tombstone; "
        f"append_tombstone(Path('{JOURNAL_CONTAINER}'), "
        f"instance_id=UUID('{INSTANCE_ID}'), account_id=UUID('{OWNER_ID}'), "
        f"accepted_at=datetime.fromisoformat('{ACCEPTED_AT}'.replace('Z', '+00:00')))"
    )
    run(
        scenario.compose(
            "run",
            "--rm",
            "--no-deps",
            "--volume",
            f"{journal.parent}:/sidebyside-journal",
            "api",
            "python",
            "-c",
            code,
        ),
        action="Synthetic deletion tombstone append",
    )
    if not journal.is_file():
        raise AcceptanceError("Synthetic deletion journal was not created.")


def _reconcile(scenario: Scenario, journal: Path) -> None:
    run(
        [
            sys.executable,
            str(RECONCILE_SCRIPT),
            "--compose-file",
            str(ROOT / "compose.yaml"),
            "--env-file",
            str(scenario.env_file),
            "--confirm-project",
            scenario.project_name,
            "--journal",
            str(journal),
            "--confirm-instance-id",
            INSTANCE_ID,
        ],
        action="Account deletion restore reconciliation",
        diagnostic_markers=(
            "The protected deletion journal does not exist.",
            "Deletion journal belongs to a different instance.",
            "Account deletion reconciliation failed",
        ),
    )


def _psql_scalar(scenario: Scenario, query: str) -> str:
    output = run(
        scenario.compose(
            "exec",
            "-T",
            "postgres",
            "psql",
            "--no-password",
            "--tuples-only",
            "--no-align",
            "--set",
            "ON_ERROR_STOP=1",
            "--username",
            "sidebyside",
            "--dbname",
            "sidebyside",
            "--command",
            query,
        ),
        action="Deletion reconciliation database assertion",
    )
    return output.decode("utf-8").strip()


def _expect_scalar(scenario: Scenario, query: str, expected: str) -> None:
    if _psql_scalar(scenario, query) != expected:
        raise AcceptanceError("A deletion reconciliation database invariant failed.")


def _verify_reconciled_state(scenario: Scenario, stale_owner_token: str) -> None:
    scenario.request(
        "/api/v1/auth/sign-in",
        expected_status=401,
        method="POST",
        payload={
            "email": OWNER_EMAIL,
            "password": "recovery-fixture-password",
            "deviceName": "Deleted recovery owner",
            "platform": "ops-acceptance",
        },
    )
    scenario.request(
        f"/api/v1/spaces/{SPACE_ID}/memories/{MEMORY_ID}",
        expected_status=401,
        bearer=stale_owner_token,
    )

    partner_token = scenario.sign_in(PARTNER_EMAIL)
    try:
        scenario.request(
            f"/api/v1/spaces/{SPACE_ID}/memories/{MEMORY_ID}",
            expected_status=200,
            bearer=partner_token,
        )
        original = scenario.request(
            f"/api/v1/spaces/{SPACE_ID}/attachments/{ATTACHMENT_ID}/content",
            expected_status=200,
            bearer=partner_token,
        )
        if original != DURABLE_ORIGINAL:
            raise AcceptanceError("Retained shared media changed during deletion reconciliation.")
    finally:
        scenario.request(
            "/api/v1/auth/sign-out",
            expected_status=204,
            method="POST",
            bearer=partner_token,
        )

    _expect_scalar(
        scenario,
        f"SELECT count(*) FROM accounts WHERE id = '{OWNER_ID}'::uuid "
        "AND disabled_at IS NOT NULL AND display_name = 'Deleted account'",
        "1",
    )
    _expect_scalar(
        scenario,
        f"SELECT count(*) FROM account_emails WHERE account_id = '{OWNER_ID}'::uuid",
        "0",
    )
    _expect_scalar(
        scenario,
        f"SELECT count(*) FROM auth_identities WHERE account_id = '{OWNER_ID}'::uuid",
        "0",
    )
    _expect_scalar(
        scenario,
        f"SELECT count(*) FROM memberships WHERE account_id = '{OWNER_ID}'::uuid "
        "AND status = 'LEFT'",
        "1",
    )
    _expect_scalar(
        scenario,
        f"SELECT count(*) FROM heart_moments WHERE id = '{PRIVATE_HEART_ID}'::uuid",
        "0",
    )
    _expect_scalar(
        scenario,
        f"SELECT count(*) FROM memories WHERE id = '{MEMORY_ID}'::uuid",
        "1",
    )
    _expect_scalar(
        scenario,
        f"SELECT count(*) FROM heart_moments WHERE id = '{PARTNER_PRIVATE_HEART_ID}'::uuid",
        "1",
    )
    _expect_scalar(
        scenario,
        f"SELECT status FROM account_deletions WHERE account_id = '{OWNER_ID}'::uuid",
        "PENDING",
    )


def run_acceptance() -> None:
    project_name = "sbs-deletion-recovery-acceptance"
    api_port = available_port()
    web_port = available_port()
    if api_port == web_port:
        web_port = available_port()

    with tempfile.TemporaryDirectory(prefix="sidebyside-deletion-recovery-") as temp_name:
        temp = Path(temp_name)
        env_file = temp / "synthetic.env"
        archive = temp / "pre-deletion-backup.tar"
        journal = temp / "protected-journal" / "deletions.jsonl"
        write_environment(env_file, project_name, api_port, web_port)
        scenario = Scenario(
            project_name=project_name,
            env_file=env_file,
            api_port=api_port,
            web_port=web_port,
        )
        try:
            scenario.start_stack(build=True)
            scenario.fixture("seed-current")
            stale_owner_token = scenario.sign_in(OWNER_EMAIL)
            scenario.backup(archive)

            # The irreversible deletion happens after this recovery point.
            # Only the forward journal therefore knows about it.
            _append_synthetic_tombstone(scenario, journal)

            scenario.cleanup()
            scenario.start_postgres()
            scenario.restore(archive)
            _reconcile(scenario, journal)
            scenario.start_stack(build=False)
            _verify_reconciled_state(scenario, stale_owner_token)
        finally:
            scenario.cleanup()


def main() -> int:
    try:
        run_acceptance()
    except AcceptanceError as exc:
        print(f"Account deletion recovery acceptance failed: {exc}", file=sys.stderr)
        return 1
    print("Account deletion recovery acceptance completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
