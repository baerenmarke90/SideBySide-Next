"""The public demo cannot be made unresettable by an ordinary visitor.

The demo resolves its two reserved personas by their reserved address and then
refuses to run unless each still carries its canonical display name. Everything
a visitor does inside the Space is disposable, because the reset replaces the
Space wholesale, but that Account-global name is the one thing the reset cannot
rebuild. A visitor who changed it would break every later reset for everybody.

Every check here goes through the HTTP API with a real bearer token, because a
client that hides the control is not the boundary: a visitor holds an ordinary
session and can call the endpoint directly.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.config import Environment, Settings
from sidebyside.demo import canonical
from sidebyside.demo.canonical import ALEX_EMAIL, ALEX_NAME, LEA_EMAIL, LEA_NAME
from sidebyside.demo.service import create_demo_space, reset_demo_space
from sidebyside.identity import service as identity_service
from sidebyside.identity.models import Account
from sidebyside.profiles.models import (
    PreferenceCategory,
    PreferenceSentiment,
    ProfileVisibility,
)
from sidebyside.relationship import offboarding
from sidebyside.relationship.models import Membership, MembershipStatus
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

REFERENCE_DATE = date(2026, 8, 24)
DEMO_PASSWORD = "canonical-demo-guard-test-password"


def profile_path(space_id: object, account_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/profiles/{account_id}"


def seed(session: Session):  # type: ignore[no-untyped-def]
    return create_demo_space(
        session,
        environment=Environment.TEST,
        lea_password=DEMO_PASSWORD,
        alex_password=DEMO_PASSWORD,
        reference_date=REFERENCE_DATE,
    )


def preference_payload(account_id: object) -> dict[str, object]:
    """A perfectly ordinary Space-scoped write the reset replaces wholesale."""
    return {
        "accountId": str(account_id),
        "visibility": ProfileVisibility.SELF_PROFILE.value,
        "category": PreferenceCategory.FOOD.value,
        "sentiment": PreferenceSentiment.LIKE.value,
        "topic": "Zimtschnecken",
        "value": "Am liebsten sonntags.",
    }


def demo_deployment(monkeypatch: pytest.MonkeyPatch, *, enabled: bool = True) -> None:
    """Make the guard see the deployment the public demo actually runs as."""
    settings = Settings.model_validate({"demo_mode": True}) if enabled else Settings()
    monkeypatch.setattr(canonical, "get_settings", lambda: settings)


def account_by_email(session: Session, email: str) -> Account:
    account = identity_service.find_by_email(session, email)
    assert account is not None
    return account


def space_of(session: Session, account: Account):  # type: ignore[no-untyped-def]
    return session.execute(
        select(Membership.space_id).where(
            Membership.account_id == account.id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
    ).scalar_one()


@pytest.fixture
def demo(session: Session, monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """A seeded canonical demo running as the public demo deployment."""
    seed(session)
    demo_deployment(monkeypatch)
    lea = account_by_email(session, LEA_EMAIL)
    alex = account_by_email(session, ALEX_EMAIL)
    return {
        "lea": lea,
        "alex": alex,
        "space_id": space_of(session, lea),
        "lea_token": sign_in(session, lea),
        "alex_token": sign_in(session, alex),
    }


def rename(client, demo, persona: str, new_name: str):  # type: ignore[no-untyped-def]
    account = demo[persona]
    current = client.get(
        profile_path(demo["space_id"], account.id),
        headers=auth(demo[f"{persona}_token"]),
    )
    assert current.status_code == 200, current.text
    return client.patch(
        profile_path(demo["space_id"], account.id),
        json={"displayName": new_name},
        headers={
            **auth(demo[f"{persona}_token"]),
            "If-Match": current.headers["etag"],
        },
    )


class TestCanonicalIdentityIsImmutable:
    def test_demo_lea_cannot_rename_herself(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        response = rename(client, demo, "lea", "Nicht mehr Lea")

        assert response.status_code == 403, response.text
        assert response.json()["code"] == "DEMO_CANONICAL_IDENTITY_IMMUTABLE"

    def test_demo_alex_cannot_rename_himself(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        response = rename(client, demo, "alex", "Nicht mehr Alex")

        assert response.status_code == 403, response.text
        assert response.json()["code"] == "DEMO_CANONICAL_IDENTITY_IMMUTABLE"

    def test_rejection_changes_neither_name_nor_version(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        "A refused mutation must not consume the Account-global version either."
        before = session.get(Account, demo["lea"].id)
        assert before is not None
        version_before = before.version

        assert rename(client, demo, "lea", "Nicht mehr Lea").status_code == 403

        session.expire_all()
        after = session.get(Account, demo["lea"].id)
        assert after is not None
        assert after.display_name == LEA_NAME
        assert after.version == version_before

    def test_refusal_names_no_internal_reserved_state(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        """The personas are public; the identifiers behind them are not.

        The entry page offers Lea and Alex by name and `docs/DEMO-SPACE.md`
        documents that the demo resets, so explaining the refusal in those
        terms discloses nothing. The reserved addresses and the internal
        Account and Space identifiers stay out of it, and the response is the
        same whichever persona is signed in.
        """
        response = rename(client, demo, "lea", "Nicht mehr Lea")

        assert LEA_EMAIL not in response.text
        assert ALEX_EMAIL not in response.text
        assert str(demo["lea"].id) not in response.text
        assert str(demo["alex"].id) not in response.text
        assert str(demo["space_id"]) not in response.text

    def test_keeping_the_canonical_name_is_not_a_mutation(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        "A save that leaves the name alone must not be refused."
        response = rename(client, demo, "lea", LEA_NAME)

        assert response.status_code == 200, response.text
        assert response.json()["displayName"] == LEA_NAME


class TestPermittedDemoMutationsRemainOpen:
    def test_space_content_stays_editable(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        "Only the reset-critical identity is protected, not the demo itself."
        response = client.post(
            f"/api/v1/spaces/{demo['space_id']}/profile-preferences",
            json=preference_payload(demo["lea"].id),
            headers=auth(demo["lea_token"]),
        )

        assert response.status_code == 201, response.text

    def test_avatar_stays_removable(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        """The avatar is Account-global but the reset purges it with the Space.

        It therefore stays mutable: the guard protects what the reset cannot
        rebuild, not everything that happens to live on the Account.
        """
        current = client.get(
            profile_path(demo["space_id"], demo["lea"].id),
            headers=auth(demo["lea_token"]),
        )
        response = client.patch(
            profile_path(demo["space_id"], demo["lea"].id),
            json={"profileAttachmentId": None},
            headers={**auth(demo["lea_token"]), "If-Match": current.headers["etag"]},
        )

        assert response.status_code == 200, response.text


class TestOrdinaryDeploymentsAreUnaffected:
    def test_a_normal_account_still_renames_itself(self, client, session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        "Nothing about this guard applies where no reserved persona exists."
        demo_deployment(monkeypatch, enabled=False)
        anna = make_account(session, "Anna")
        space = make_space(session, anna)
        token = sign_in(session, anna)

        current = client.get(profile_path(space.id, anna.id), headers=auth(token))
        response = client.patch(
            profile_path(space.id, anna.id),
            json={"displayName": "Änne"},
            headers={**auth(token), "If-Match": current.headers["etag"]},
        )

        assert response.status_code == 200, response.text
        assert response.json()["displayName"] == "Änne"

    def test_a_normal_account_renames_itself_inside_a_demo_deployment(
        self, client, session, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        "The guard is about the reserved identities, not about demo mode."
        demo_deployment(monkeypatch)
        anna = make_account(session, "Anna")
        space = make_space(session, anna)
        token = sign_in(session, anna)

        current = client.get(profile_path(space.id, anna.id), headers=auth(token))
        response = client.patch(
            profile_path(space.id, anna.id),
            json={"displayName": "Änne"},
            headers={**auth(token), "If-Match": current.headers["etag"]},
        )

        assert response.status_code == 200, response.text

    def test_the_reserved_persona_renames_outside_a_demo_deployment(
        self, client, session, monkeypatch
    ) -> None:  # type: ignore[no-untyped-def]
        """Development keeps the existing contract.

        Outside a demo deployment the reset's own fail-closed validation stays
        the operator-facing protection, exactly as for the Account-deletion and
        Space-offboarding guards, which are also deployment-scoped.
        """
        seed(session)
        demo_deployment(monkeypatch, enabled=False)
        lea = account_by_email(session, LEA_EMAIL)
        token = sign_in(session, lea)
        space_id = space_of(session, lea)

        current = client.get(profile_path(space_id, lea.id), headers=auth(token))
        response = client.patch(
            profile_path(space_id, lea.id),
            json={"displayName": "Lokale QA"},
            headers={**auth(token), "If-Match": current.headers["etag"]},
        )

        assert response.status_code == 200, response.text


class TestExistingDemoGuardsRemainIntact:
    def test_space_offboarding_stays_blocked(self, session, monkeypatch, demo) -> None:  # type: ignore[no-untyped-def]
        from sidebyside.core.errors import ForbiddenError

        with pytest.raises(ForbiddenError) as rejected:
            offboarding.leave_space(session, demo["lea"], demo["space_id"])

        assert rejected.value.code == "SPACE_OFFBOARDING_DEMO_FORBIDDEN"

    def test_account_self_deletion_stays_blocked(self, session, monkeypatch, demo) -> None:  # type: ignore[no-untyped-def]
        from sidebyside.core.errors import ForbiddenError
        from sidebyside.identity import deletion_self_service

        monkeypatch.setattr(
            deletion_self_service.canonical,
            "get_settings",
            lambda: Settings.model_validate({"demo_mode": True}),
        )

        with pytest.raises(ForbiddenError) as rejected:
            deletion_self_service.accept_self_deletion(demo["lea"].id)

        assert rejected.value.code == "ACCOUNT_DELETION_DEMO_FORBIDDEN"


class TestResetStaysUsableAndFailsClosed:
    def test_reset_still_runs_after_permitted_demo_mutations(self, client, session, demo) -> None:  # type: ignore[no-untyped-def]
        "Everything a visitor is still allowed to do must remain resettable."
        assert (
            client.post(
                f"/api/v1/spaces/{demo['space_id']}/profile-preferences",
                json=preference_payload(demo["lea"].id),
                headers=auth(demo["lea_token"]),
            ).status_code
            == 201
        )
        assert rename(client, demo, "lea", LEA_NAME).status_code == 200

        result = reset_demo_space(
            session,
            environment=Environment.TEST,
            reference_date=REFERENCE_DATE,
        )

        assert result.space_id != demo["space_id"]
        session.expire_all()
        assert account_by_email(session, LEA_EMAIL).display_name == LEA_NAME
        assert account_by_email(session, ALEX_EMAIL).display_name == ALEX_NAME

    def test_reset_still_refuses_a_genuinely_corrupted_identity(self, session, demo) -> None:  # type: ignore[no-untyped-def]
        """The guard does not replace the reset's own validation.

        An operator or a direct database edit can still produce a drifted
        identity, and the reset must keep refusing rather than guessing which
        Account was meant.
        """
        corrupted = account_by_email(session, LEA_EMAIL)
        corrupted.display_name = "Von Hand veraendert"
        session.flush()

        with pytest.raises(RuntimeError, match="non-demo display name"):
            reset_demo_space(
                session,
                environment=Environment.TEST,
                reference_date=REFERENCE_DATE,
            )


class TestGuardPrimitive:
    def test_only_reserved_addresses_are_canonical(self, session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        "Recognition follows the reserved address, never the current name."
        seed(session)
        demo_deployment(monkeypatch)
        lea = account_by_email(session, LEA_EMAIL)
        impostor = make_account(session, LEA_NAME)

        assert canonical.is_canonical_reserved_account(session, lea) is True
        assert canonical.is_canonical_reserved_account(session, impostor) is False

    def test_recognition_survives_a_name_that_already_drifted(self, session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        "Otherwise the guard would stop working exactly once it was needed."
        seed(session)
        demo_deployment(monkeypatch)
        lea = account_by_email(session, LEA_EMAIL)
        lea.display_name = "Bereits abgewichen"
        session.flush()

        assert canonical.is_canonical_reserved_account(session, lea) is True
