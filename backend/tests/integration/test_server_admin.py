"""ServerAdmin authorization and privacy-safe operational projections."""

from __future__ import annotations

import pytest

from sidebyside.config import get_settings
from sidebyside.core.clock import now
from sidebyside.identity.models import AccountEmail
from sidebyside.jobs.models import Job, JobStatus
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

ADMIN_EMAIL = "operator@example.test"


@pytest.fixture
def server_admin_allowlist(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SBS_SERVER_ADMIN_EMAILS", f'["{ADMIN_EMAIL}"]')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _add_email(session, account, *, verified: bool) -> AccountEmail:  # type: ignore[no-untyped-def]
    address = AccountEmail(
        account_id=account.id,
        email=ADMIN_EMAIL,
        is_primary=True,
        verified_at=now() if verified else None,
    )
    session.add(address)
    session.flush()
    return address


def test_server_admin_endpoints_require_authentication(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/server-admin/overview")

    assert response.status_code == 401


def test_allowlisted_but_unverified_email_does_not_grant_server_admin(
    client,
    session,
    server_admin_allowlist,
) -> None:  # type: ignore[no-untyped-def]
    account = make_account(session, "Operator")
    _add_email(session, account, verified=False)
    token = sign_in(session, account)

    capability = client.get("/api/v1/auth/capabilities", headers=auth(token))
    overview = client.get("/api/v1/server-admin/overview", headers=auth(token))

    assert capability.status_code == 200
    assert capability.json() == {"serverAdmin": False}
    assert overview.status_code == 403
    assert overview.json()["code"] == "SERVER_ADMIN_REQUIRED"


def test_verified_allowlisted_account_gets_server_admin_capability(
    client,
    session,
    server_admin_allowlist,
) -> None:  # type: ignore[no-untyped-def]
    account = make_account(session, "Operator")
    _add_email(session, account, verified=True)
    make_space(session, account)
    token = sign_in(session, account)

    capability = client.get("/api/v1/auth/capabilities", headers=auth(token))
    overview = client.get("/api/v1/server-admin/overview", headers=auth(token))

    assert capability.status_code == 200
    assert capability.json() == {"serverAdmin": True}
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["applicationStatus"] == "ok"
    assert payload["databaseStatus"] == "ok"
    assert payload["deployment"] == "self_hosted"
    assert payload["accountCount"] == 1
    assert payload["activeSpaceCount"] == 1


def test_server_admin_overview_never_exposes_job_payload_or_raw_error(
    client,
    session,
    server_admin_allowlist,
) -> None:  # type: ignore[no-untyped-def]
    account = make_account(session, "Operator")
    _add_email(session, account, verified=True)
    token = sign_in(session, account)

    secret_payload = "owner-only-payload-must-not-leak"
    secret_error = "postgresql://secret-user:secret-password@private-host/db"
    session.add(
        Job(
            kind="safe-kind",
            payload={"private": secret_payload},
            status=JobStatus.FAILED.value,
            attempts=3,
            max_attempts=3,
            last_error=secret_error,
            finished_at=now(),
        )
    )
    session.flush()

    response = client.get("/api/v1/server-admin/overview", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["jobsFailed"] == 1
    assert payload["recentFailedJobs"][0]["kind"] == "safe-kind"
    assert "payload" not in payload["recentFailedJobs"][0]
    assert "lastError" not in payload["recentFailedJobs"][0]
    assert secret_payload not in response.text
    assert secret_error not in response.text
