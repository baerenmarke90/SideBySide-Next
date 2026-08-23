"""Geraetesitzungen: anlegen, pruefen, erneuern, widerrufen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth.tokens import (
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_BYTES,
    REFRESH_TOKEN_LIFETIME,
    generate_token,
    hash_token,
)
from sidebyside.core.clock import now
from sidebyside.core.errors import ErrorCode, UnauthenticatedError
from sidebyside.identity.models import Account, DeviceSession


@dataclass(frozen=True)
class IssuedTokens:
    """Was der Client bekommt. Der Klartext existiert nur hier."""

    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


def start_session(
    session: Session, account: Account, *, device_name: str = "", platform: str = ""
) -> tuple[DeviceSession, IssuedTokens]:
    """Eine neue Sitzung eroeffnen.

    Wird von den Anmeldewegen aufgerufen, sobald die Identitaet feststeht.
    Diese Funktion prueft KEINE Identitaet - sie setzt voraus, dass das
    bereits geschehen ist.
    """
    access = generate_token()
    refresh = generate_token(REFRESH_TOKEN_BYTES)
    jetzt = now()

    geraet = DeviceSession(
        account_id=account.id,
        device_name=device_name[:120],
        platform=platform[:32],
        refresh_token_hash=hash_token(refresh),
        access_token_hash=hash_token(access),
        access_expires_at=jetzt + ACCESS_TOKEN_LIFETIME,
        expires_at=jetzt + REFRESH_TOKEN_LIFETIME,
        last_used_at=jetzt,
    )
    session.add(geraet)

    return geraet, IssuedTokens(
        access_token=access,
        refresh_token=refresh,
        access_expires_at=geraet.access_expires_at or jetzt,
        refresh_expires_at=geraet.expires_at,
    )


def authenticate(session: Session, access_token: str) -> Account:
    """Der Account zu einem Access Token."""
    return resolve(session, access_token)[1]


def resolve(session: Session, access_token: str) -> tuple[DeviceSession, Account]:
    """Sitzung und Account zu einem Access Token ermitteln.

    Jeder Fehlschlag ergibt dieselbe Meldung. Ein Aufrufer soll nicht
    unterscheiden koennen, ob ein Token unbekannt, abgelaufen oder
    widerrufen ist - das waere eine Auskunft ueber gueltige Token.
    """
    if not access_token:
        raise UnauthenticatedError("Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED)

    geraet = session.execute(
        select(DeviceSession).where(DeviceSession.access_token_hash == hash_token(access_token))
    ).scalar_one_or_none()

    jetzt = now()
    if (
        geraet is None
        or geraet.revoked_at is not None
        or geraet.access_expires_at is None
        or geraet.access_expires_at <= jetzt
    ):
        raise UnauthenticatedError("Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED)

    account = session.get(Account, geraet.account_id)
    if account is None or not account.is_active:
        raise UnauthenticatedError("Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED)

    geraet.last_used_at = jetzt
    return geraet, account


def refresh_session(session: Session, refresh_token: str) -> IssuedTokens:
    """Die Sitzung erneuern und beide Token rotieren.

    Replay-Erkennung: taucht ein bereits rotierter Refresh Token wieder auf,
    ist er kopiert worden - der rechtmaessige Client haette den neuen. Die
    Sitzung wird dann sofort widerrufen, statt dem Angreifer und dem
    Besitzer nebeneinander Zugang zu lassen.
    """
    gehasht = hash_token(refresh_token) if refresh_token else ""
    gescheitert = UnauthenticatedError(
        "Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED
    )
    if not gehasht:
        raise gescheitert

    jetzt = now()

    wiederverwendet = session.execute(
        select(DeviceSession).where(DeviceSession.previous_refresh_token_hash == gehasht)
    ).scalar_one_or_none()
    if wiederverwendet is not None:
        revoke(wiederverwendet)
        raise gescheitert

    geraet = session.execute(
        select(DeviceSession).where(DeviceSession.refresh_token_hash == gehasht)
    ).scalar_one_or_none()

    if geraet is None or geraet.revoked_at is not None or geraet.expires_at <= jetzt:
        raise gescheitert

    account = session.get(Account, geraet.account_id)
    if account is None or not account.is_active:
        raise gescheitert

    access = generate_token()
    refresh_neu = generate_token(REFRESH_TOKEN_BYTES)

    geraet.previous_refresh_token_hash = geraet.refresh_token_hash
    geraet.refresh_token_hash = hash_token(refresh_neu)
    geraet.access_token_hash = hash_token(access)
    geraet.access_expires_at = jetzt + ACCESS_TOKEN_LIFETIME
    geraet.expires_at = jetzt + REFRESH_TOKEN_LIFETIME
    geraet.last_used_at = jetzt

    return IssuedTokens(
        access_token=access,
        refresh_token=refresh_neu,
        access_expires_at=geraet.access_expires_at,
        refresh_expires_at=geraet.expires_at,
    )


def revoke(device_session: DeviceSession) -> None:
    """Eine Sitzung beenden.

    Der Access Token wird mit entwertet, nicht nur der Refresh Token - sonst
    liefe ein gestohlenes Geraet noch bis zum Ablauf weiter.
    """
    device_session.revoked_at = now()
    device_session.access_token_hash = None
    device_session.access_expires_at = None


def revoke_all(session: Session, account: Account) -> int:
    """Alle Sitzungen eines Accounts beenden."""
    offen = (
        session.execute(
            select(DeviceSession).where(
                DeviceSession.account_id == account.id,
                DeviceSession.revoked_at.is_(None),
            )
        )
        .scalars()
        .all()
    )

    for geraet in offen:
        revoke(geraet)
    return len(offen)
