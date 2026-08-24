"""HTTP-Matrix fuer PartnerProfile und ProfilePreference."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


def preference_body(
    account_id: object,
    *,
    visibility: str = "SELF_PROFILE",
    category: str = "DRINK",
    topic: str = "favorite_drink",
    sentiment: str = "LOVE",
    value: str = "Coca Cola Zero",
) -> dict[str, Any]:
    return {
        "accountId": str(account_id),
        "visibility": visibility,
        "category": category,
        "topic": topic,
        "sentiment": sentiment,
        "value": value,
    }


def preferences_path(space_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/profile-preferences"


def profile_path(space_id: object, account_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/profiles/{account_id}"


@pytest.fixture
def paar(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremd")

    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    fremder_space = make_space(session, fremd)
    session.flush()

    return {
        "anna": anna,
        "ben": ben,
        "fremd": fremd,
        "space": space,
        "fremder_space": fremder_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_fremd": sign_in(session, fremd),
    }


def create_preference(client, paar, *, token_key: str = "token_a", **overrides):  # type: ignore[no-untyped-def]
    body = preference_body(paar["anna"].id)
    body.update(overrides)
    return client.post(
        preferences_path(paar["space"].id),
        json=body,
        headers=auth(paar[token_key]),
    )


class TestPartnerProfile:
    def test_membership_erzeugt_uuidv7_profile(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.get(
            profile_path(paar["space"].id, paar["ben"].id),
            headers=auth(paar["token_a"]),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["accountId"] == str(paar["ben"].id)
        assert body["displayName"] == "Ben"
        assert body["preferences"] == []
        assert UUID(body["id"]).version == 7

    def test_partner_sieht_self_profile_preference(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = create_preference(client, paar)
        assert created.status_code == 201

        response = client.get(
            profile_path(paar["space"].id, paar["anna"].id),
            headers=auth(paar["token_b"]),
        )
        assert response.status_code == 200
        assert [item["value"] for item in response.json()["preferences"]] == ["Coca Cola Zero"]

    def test_private_partner_note_erscheint_nie_im_partnerprofil(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = create_preference(
            client,
            paar,
            accountId=str(paar["ben"].id),
            visibility="PRIVATE_PARTNER_NOTE",
            category="OTHER",
            topic="surprise",
            sentiment="LIKE",
            value="Ueberraschung planen",
        )
        assert created.status_code == 201

        response = client.get(
            profile_path(paar["space"].id, paar["ben"].id),
            headers=auth(paar["token_a"]),
        )
        assert response.status_code == 200
        assert response.json()["preferences"] == []

    def test_cross_tenant_profile_bleibt_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.get(
            profile_path(paar["space"].id, paar["fremd"].id),
            headers=auth(paar["token_a"]),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "PARTNER_PROFILE_NOT_FOUND"


class TestPreferencePrivacy:
    def test_partner_kann_fremdes_self_profile_nicht_schreiben(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.post(
            preferences_path(paar["space"].id),
            json=preference_body(paar["anna"].id),
            headers=auth(paar["token_b"]),
        )
        assert response.status_code == 403
        assert response.json()["code"] == "PROFILE_SELF_WRITE_ONLY"

    def test_private_note_ist_fuer_betroffenen_partner_unsichtbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = client.post(
            preferences_path(paar["space"].id),
            json=preference_body(
                paar["ben"].id,
                visibility="PRIVATE_PARTNER_NOTE",
                category="OTHER",
                topic="gift",
                sentiment="LOVE",
                value="Geheime Geschenkidee",
            ),
            headers=auth(paar["token_a"]),
        )
        assert created.status_code == 201
        preference_id = created.json()["id"]

        owner_list = client.get(preferences_path(paar["space"].id), headers=auth(paar["token_a"]))
        partner_list = client.get(preferences_path(paar["space"].id), headers=auth(paar["token_b"]))
        assert [item["id"] for item in owner_list.json()] == [preference_id]
        assert partner_list.json() == []

        direct = client.get(
            f"{preferences_path(paar['space'].id)}/{preference_id}",
            headers=auth(paar["token_b"]),
        )
        assert direct.status_code == 404
        assert direct.json()["code"] == "PROFILE_PREFERENCE_NOT_FOUND"

    def test_cross_tenant_preference_ist_404(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = create_preference(client, paar)
        preference_id = created.json()["id"]
        response = client.get(
            f"/api/v1/spaces/{paar['fremder_space'].id}/profile-preferences/{preference_id}",
            headers=auth(paar["token_fremd"]),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "PROFILE_PREFERENCE_NOT_FOUND"

    def test_geteilte_preference_ist_fuer_partner_nur_lesbar(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = create_preference(client, paar)
        preference_id = created.json()["id"]
        response = client.put(
            f"{preferences_path(paar['space'].id)}/{preference_id}",
            json={
                "category": "DRINK",
                "topic": "favorite_drink",
                "sentiment": "LIKE",
                "value": "Wasser",
            },
            headers={**auth(paar["token_b"]), "If-Match": '"1"'},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "NOT_RESOURCE_OWNER"

    def test_malformed_und_unsichtbar_sind_gleiche_404_klasse(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.get(
            f"{preferences_path(paar['space'].id)}/keine-uuid",
            headers=auth(paar["token_b"]),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "PROFILE_PREFERENCE_NOT_FOUND"


class TestPreferenceConcurrencyUndValidation:
    def test_update_braucht_aktuelle_version(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        created = create_preference(client, paar)
        preference_id = created.json()["id"]
        path = f"{preferences_path(paar['space'].id)}/{preference_id}"
        update_body = {
            "category": "DRINK",
            "topic": "favorite_drink",
            "sentiment": "LIKE",
            "value": "Mineralwasser",
        }

        updated = client.put(
            path,
            json=update_body,
            headers={**auth(paar["token_a"]), "If-Match": '"1"'},
        )
        assert updated.status_code == 200
        assert updated.json()["version"] == 2
        assert updated.headers["ETag"] == '"2"'

        stale = client.put(
            path,
            json=update_body,
            headers={**auth(paar["token_a"]), "If-Match": '"1"'},
        )
        assert stale.status_code == 409
        assert stale.json()["code"] == "VERSION_CONFLICT"

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("category", "UNKNOWN"),
            ("sentiment", "OBSESSED"),
            ("visibility", "PUBLIC"),
        ],
    )
    def test_unbekannte_enums_werden_abgewiesen(self, client, paar, field: str, value: str) -> None:  # type: ignore[no-untyped-def]
        body = preference_body(paar["anna"].id)
        body[field] = value
        response = client.post(
            preferences_path(paar["space"].id),
            json=body,
            headers=auth(paar["token_a"]),
        )
        assert response.status_code == 422
        assert set(response.json()) == {"type", "title", "status", "detail", "code"}

    def test_private_note_ueber_sich_selbst_wird_abgewiesen(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.post(
            preferences_path(paar["space"].id),
            json=preference_body(paar["anna"].id, visibility="PRIVATE_PARTNER_NOTE"),
            headers=auth(paar["token_a"]),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "PROFILE_PARTNER_NOTE_TARGET_REQUIRED"

    def test_anonym_bleibt_401(self, client, paar) -> None:  # type: ignore[no-untyped-def]
        response = client.get(preferences_path(paar["space"].id))
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
