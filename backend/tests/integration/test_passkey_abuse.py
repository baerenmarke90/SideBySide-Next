"""DB-weite Abuse-Grenze fuer anonyme Passkey-Authentication-Starts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from sidebyside.auth import passkey_abuse, passkeys
from sidebyside.auth.tokens import hash_token
from sidebyside.core.errors import RateLimitedError
from sidebyside.identity.models import RateLimitEvent, WebAuthnChallenge
from tests.conftest import requires_database

pytestmark = [pytest.mark.integration, requires_database]

START = "/api/v1/auth/passkeys/authentication/start"


def _count_challenges(session) -> int:  # type: ignore[no-untyped-def]
    return session.execute(select(func.count()).select_from(WebAuthnChallenge)).scalar_one()


def _count_events(session, key: str) -> int:  # type: ignore[no-untyped-def]
    return session.execute(
        select(func.count())
        .select_from(RateLimitEvent)
        .where(
            RateLimitEvent.action == passkey_abuse.ACTION_AUTHENTICATION_START,
            RateLimitEvent.key_hash == hash_token(key.lower()),
        )
    ).scalar_one()


def test_postgresql_sperrschwelle_verhindert_weitere_challenges(session) -> None:  # type: ignore[no-untyped-def]
    """Nach dem letzten Slot darf die Fachlogik keine weitere Challenge schreiben."""
    client_host = "198.51.100.10"
    key = passkey_abuse.network_key(client_host)

    for _ in range(passkey_abuse.AUTHENTICATION_START.attempts):
        passkey_abuse.reserve_authentication_start(session, client_host)
        passkeys.start_authentication(session)

    assert _count_challenges(session) == passkey_abuse.AUTHENTICATION_START.attempts
    assert _count_events(session, key) == passkey_abuse.AUTHENTICATION_START.attempts

    with pytest.raises(RateLimitedError):
        passkey_abuse.reserve_authentication_start(session, client_host)

    assert _count_challenges(session) == passkey_abuse.AUTHENTICATION_START.attempts
    assert _count_events(session, key) == passkey_abuse.AUTHENTICATION_START.attempts


def test_ein_begrenztes_netz_blockiert_nicht_alle_anmeldungen(session) -> None:  # type: ignore[no-untyped-def]
    """Der Abuse-Key ist pro Netzwerkidentitaet und kein globaler Kill-Switch."""
    blockiert = "198.51.100.10"
    anderes_netz = "198.51.100.11"

    for _ in range(passkey_abuse.AUTHENTICATION_START.attempts):
        passkey_abuse.reserve_authentication_start(session, blockiert)
        passkeys.start_authentication(session)

    with pytest.raises(RateLimitedError):
        passkey_abuse.reserve_authentication_start(session, blockiert)

    passkey_abuse.reserve_authentication_start(session, anderes_netz)
    passkeys.start_authentication(session)

    assert _count_challenges(session) == passkey_abuse.AUTHENTICATION_START.attempts + 1


def test_paralleler_http_burst_ueberschreitet_die_schwelle_nicht(production_client) -> None:  # type: ignore[no-untyped-def]
    """Echte Request-UoWs teilen sich die atomare DB-weite Restkapazitaet."""
    client, maker = production_client
    restkapazitaet = 2
    vorfuellen = passkey_abuse.AUTHENTICATION_START.attempts - restkapazitaet

    for _ in range(vorfuellen):
        antwort = client.post(START)
        assert antwort.status_code == 201, antwort.text

    burst = 5
    start = Barrier(burst)

    def beginnen(_: int):  # type: ignore[no-untyped-def]
        start.wait(timeout=5)
        return client.post(START)

    with ThreadPoolExecutor(max_workers=burst) as pool:
        antworten = list(pool.map(beginnen, range(burst)))

    codes = sorted(antwort.status_code for antwort in antworten)
    assert codes == [201] * restkapazitaet + [429] * (burst - restkapazitaet)
    for antwort in antworten:
        if antwort.status_code == 429:
            assert antwort.json()["code"] == "RATE_LIMITED"

    # Starlette TestClient verwendet als ASGI-Peer standardmaessig
    # "testclient". Das ist absichtlich derselbe Weg wie in Produktion;
    # lediglich der Peer-Bezeichner ist hier keine IP-Adresse.
    key = passkey_abuse.network_key("testclient")
    with maker() as committed:
        assert _count_challenges(committed) == passkey_abuse.AUTHENTICATION_START.attempts
        assert _count_events(committed, key) == passkey_abuse.AUTHENTICATION_START.attempts
