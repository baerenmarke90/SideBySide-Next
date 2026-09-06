"""HTTP contract coverage for Account-deletion recent authentication."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.auth import passwords, recent_auth
from sidebyside.identity import service as accounts
from sidebyside.identity.models import RecentAuthenticationGrant
from tests.conftest import auth, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

CAPABILITIES = "/api/v1/auth/recent-authentication/account-deletion"
PASSWORD_STEP_UP = "/api/v1/auth/recent-authentication/account-deletion/password"
PASSWORD = "account deletion step-up password 667!"


def _local_account(session: Session):  # type: ignore[no-untyped-def]
    account = accounts.create_account(
        session,
        display_name="Recent HTTP",
        email="recent-http@example.org",
        password_hash=passwords.hash_password(PASSWORD),
    )
    token = sign_in(session, account)
    session.flush()
    return account, auth(token)


def test_capabilities_are_server_derived_for_the_current_account(
    client,
    session: Session,
) -> None:  # type: ignore[no-untyped-def]
    _, headers = _local_account(session)

    response = client.get(CAPABILITIES, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "localPassword": True,
        "passkey": False,
        "oidcConnections": [],
        "expiresInSeconds": int(recent_auth.RECENT_AUTH_LIFETIME.total_seconds()),
    }


def test_password_endpoint_fails_closed_then_issues_no_client_bearer_proof(
    client,
    session: Session,
) -> None:  # type: ignore[no-untyped-def]
    _, headers = _local_account(session)

    rejected = client.post(
        PASSWORD_STEP_UP,
        headers=headers,
        json={"password": "wrong"},
    )
    assert rejected.status_code == 401
    assert rejected.json()["code"] == recent_auth.RecentAuthenticationErrorCode.PASSWORD_INVALID
    assert (
        session.execute(select(func.count()).select_from(RecentAuthenticationGrant)).scalar_one()
        == 0
    )

    accepted = client.post(
        PASSWORD_STEP_UP,
        headers=headers,
        json={"password": PASSWORD},
    )
    assert accepted.status_code == 200, accepted.text
    body = accepted.json()
    assert body["purpose"] == "ACCOUNT_DELETION"
    assert body["method"] == "LOCAL_PASSWORD"
    assert set(body) == {"purpose", "method", "achievedAt", "expiresAt"}
    assert (
        session.execute(select(func.count()).select_from(RecentAuthenticationGrant)).scalar_one()
        == 1
    )
