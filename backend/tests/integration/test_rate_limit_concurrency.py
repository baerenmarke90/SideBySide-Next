"""Atomare Rate-Limit-Schwellen ueber den produktiven Request-Lifecycle."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from sidebyside.auth import rate_limit
from sidebyside.auth.tokens import hash_token
from sidebyside.identity.models import RateLimitEvent
from tests.conftest import TEST_BOOTSTRAP_TOKEN, requires_database

pytestmark = [pytest.mark.integration, requires_database]

GUTES_PASSWORT = "ein-ausreichend-langes-passwort"


def test_paralleler_burst_verbraucht_exakt_die_restlichen_slots(
    production_client,
) -> None:  # type: ignore[no-untyped-def]
    """Mehr parallele Requests als Restbudget duerfen die Schwelle nicht ueberziehen."""
    client, maker = production_client
    email = "parallel-limit@example.org"

    registrierung = client.post(
        "/api/v1/auth/register",
        json={
            "displayName": "Anna",
            "email": email,
            "password": GUTES_PASSWORT,
            "bootstrapToken": TEST_BOOTSTRAP_TOKEN,
        },
    )
    assert registrierung.status_code == 201

    restkapazitaet = 2
    vorfuellen = rate_limit.SIGN_IN.attempts - restkapazitaet
    for _ in range(vorfuellen):
        antwort = client.post(
            "/api/v1/auth/sign-in",
            json={"email": email, "password": "falsch-falsch"},
        )
        assert antwort.status_code == 401

    burst = 5
    start = Barrier(burst)

    def fehlversuch(_: int):  # type: ignore[no-untyped-def]
        start.wait(timeout=5)
        return client.post(
            "/api/v1/auth/sign-in",
            json={"email": email, "password": "falsch-falsch"},
        )

    with ThreadPoolExecutor(max_workers=burst) as pool:
        antworten = list(pool.map(fehlversuch, range(burst)))

    codes = sorted(antwort.status_code for antwort in antworten)
    erwartete_codes = [401] * restkapazitaet
    erwartete_codes.extend([429] * (burst - restkapazitaet))
    assert codes == erwartete_codes
    for antwort in antworten:
        if antwort.status_code == 429:
            assert antwort.json()["code"] == "RATE_LIMITED"
            assert email not in antwort.text

    with maker() as committed:
        versuche = committed.execute(
            select(func.count())
            .select_from(RateLimitEvent)
            .where(
                RateLimitEvent.action == "sign_in",
                RateLimitEvent.key_hash == hash_token(email),
            )
        ).scalar_one()

    assert versuche == rate_limit.SIGN_IN.attempts
