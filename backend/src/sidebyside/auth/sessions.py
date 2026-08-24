"""Geraetesitzungen: anlegen, pruefen, erneuern, widerrufen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from sqlalchemy import delete, or_, select

if TYPE_CHECKING:
    from sqlalchemy import CursorResult
from sqlalchemy.orm import Session

from sidebyside.auth.tokens import (
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_BYTES,
    REFRESH_TOKEN_LIFETIME,
    SESSION_ABSOLUTE_LIFETIME,
    generate_token,
    hash_token,
)
from sidebyside.core.clock import now
from sidebyside.core.errors import ErrorCode, UnauthenticatedError
from sidebyside.db.session import schedule_after_rollback
from sidebyside.identity.models import Account, ConsumedRefreshToken, DeviceSession

# Wie lange die Replay-Historie eine beendete Familie ueberlebt.
#
# Solange eine Sitzung laeuft, bleibt jede ihrer verbrauchten Generationen
# stehen - sonst entstuende genau die Luecke, die diese Historie schliessen
# soll. Erst wenn die Sitzung widerrufen oder abgelaufen ist, kann ein
# Replay ohnehin nichts mehr ausloesen: der Refresh scheitert dann bereits
# an der toten Sitzung. Die Frist danach ist reine Nachvollziehbarkeit.
#
# Begrenzt ist die Historie dadurch aber erst zusammen mit
# SESSION_ABSOLUTE_LIFETIME. Das gleitende Refresh-Fenster allein wuerde
# eine regelmaessig genutzte Sitzung beliebig lange am Leben halten, und
# mit ihr eine Historie, die nie geraeumt wird.
REPLAY_HISTORY_RETENTION = timedelta(days=30)


@dataclass(frozen=True)
class IssuedTokens:
    """Was der Client bekommt. Der Klartext existiert nur hier."""

    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


def _revoke_by_id(session: Session, *, device_session_id: UUID) -> None:
    device_session = session.get(DeviceSession, device_session_id)
    if device_session is not None and device_session.revoked_at is None:
        revoke(device_session)


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
        # Ab hier laeuft die Uhr der Familie. Keine Rotation stellt sie
        # zurueck.
        absolute_expires_at=jetzt + SESSION_ABSOLUTE_LIFETIME,
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
        # Sonst liefe ein kurz vor der Grenze ausgestellter Access Token
        # noch bis zu seiner eigenen Frist weiter, und die harte Obergrenze
        # waere keine.
        or geraet.absolute_expires_at <= jetzt
    ):
        raise UnauthenticatedError("Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED)

    account = session.get(Account, geraet.account_id)
    if account is None or not account.is_active:
        raise UnauthenticatedError("Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED)

    geraet.last_used_at = jetzt
    return geraet, account


def _revoke_family_on_replay(session: Session, *, token_hash: str) -> None:
    """Die Familie widerrufen, zu der ein verbrauchter Token gehoert.

    Wird nur mit einem Hash aufgerufen, der keine aktuelle Sitzung mehr
    trifft. Findet sich der Hash in der Verbrauchshistorie, war es ein
    echter Token dieser Familie - und wer ihn jetzt noch vorlegt, hat eine
    Kopie. Der rechtmaessige Client haette laengst die neue Generation.

    Der Widerruf wird zusaetzlich nach dem Rollback wiederholt: die Anfrage
    endet mit 401, und ohne diese Vormerkung ginge die
    Kompromittierungsreaktion mit der verworfenen Transaktion verloren.
    """
    familie = session.execute(
        select(ConsumedRefreshToken.device_session_id).where(
            ConsumedRefreshToken.token_hash == token_hash
        )
    ).scalar_one_or_none()
    if familie is None:
        return

    geraet = session.execute(
        select(DeviceSession).where(DeviceSession.id == familie).with_for_update()
    ).scalar_one_or_none()
    if geraet is None:
        return

    if geraet.revoked_at is None:
        revoke(geraet)
    schedule_after_rollback(session, partial(_revoke_by_id, device_session_id=familie))


def refresh_session(session: Session, refresh_token: str) -> IssuedTokens:
    """Die Sitzung erneuern und beide Token rotieren.

    Replay-Erkennung ueber die gesamte Token-Familie: die Sitzung ist die
    Familie, und jede verbrauchte Generation bleibt ihr zugeordnet. Taucht
    irgendeine davon wieder auf - auch viele Rotationen spaeter -, ist sie
    kopiert worden; der rechtmaessige Client haette die aktuelle. Die
    Sitzung wird dann widerrufen, statt dem Angreifer und dem Besitzer
    nebeneinander Zugang zu lassen.

    Nach aussen ist das nicht unterscheidbar. Unbekannt, abgelaufen,
    widerrufen und als Replay erkannt ergeben dieselbe Antwort - sonst
    verriete die Fehlermeldung, welche Token einmal echt waren.

    Die Rotation verlaengert nur das gleitende Fenster, nie die absolute
    Lebensdauer der Familie. Ist die erreicht, hilft kein Refresh mehr; es
    braucht eine neue Anmeldung und damit eine neue Familie.
    """
    gehasht = hash_token(refresh_token) if refresh_token else ""
    gescheitert = UnauthenticatedError(
        "Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED
    )
    if not gehasht:
        raise gescheitert

    jetzt = now()

    geraet = session.execute(
        select(DeviceSession).where(DeviceSession.refresh_token_hash == gehasht).with_for_update()
    ).scalar_one_or_none()

    # Kein Treffer auf die aktuelle Generation. Das ist der Weg, auf dem
    # sowohl ein alter Token als auch der Verlierer zweier paralleler
    # Rotationen ankommt: PostgreSQL prueft die Bedingung nach der Sperre
    # erneut gegen die inzwischen rotierte Zeile, sodass hier genau ein
    # Request weiterlaeuft und der andere als Replay behandelt wird.
    if geraet is None:
        _revoke_family_on_replay(session, token_hash=gehasht)
        raise gescheitert

    if (
        geraet.revoked_at is not None
        or geraet.expires_at <= jetzt
        or geraet.absolute_expires_at <= jetzt
    ):
        raise gescheitert

    account = session.get(Account, geraet.account_id)
    if account is None or not account.is_active:
        raise gescheitert

    access = generate_token()
    refresh_neu = generate_token(REFRESH_TOKEN_BYTES)

    session.add(
        ConsumedRefreshToken(
            device_session_id=geraet.id,
            token_hash=geraet.refresh_token_hash,
            consumed_at=jetzt,
        )
    )
    geraet.refresh_token_hash = hash_token(refresh_neu)
    geraet.access_token_hash = hash_token(access)
    # Beide Fenster enden spaetestens mit der Familie. Sonst nennte die
    # Antwort dem Client Ablaufdaten, die der Server nicht einhaelt.
    geraet.access_expires_at = min(jetzt + ACCESS_TOKEN_LIFETIME, geraet.absolute_expires_at)
    geraet.expires_at = min(jetzt + REFRESH_TOKEN_LIFETIME, geraet.absolute_expires_at)
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


def prune_replay_history(session: Session, older_than: datetime | None = None) -> int:
    """Verbrauchte Generationen beendeter Familien entfernen.

    Fuer einen Hintergrundjob gedacht. Laufende Sitzungen bleiben
    unangetastet - deren Historie ist die Replay-Erkennung selbst.
    """
    grenze = older_than or (now() - REPLAY_HISTORY_RETENTION)

    # NULL-Vergleiche treffen nicht: eine laufende Sitzung ohne
    # ``revoked_at`` faellt allein ueber ``expires_at``, und auch nur wenn
    # sie tatsaechlich abgelaufen ist.
    beendet = select(DeviceSession.id).where(
        or_(DeviceSession.revoked_at < grenze, DeviceSession.expires_at < grenze)
    )

    # session.execute ist allgemein typisiert; ein DELETE liefert ein
    # CursorResult mit rowcount.
    ergebnis = cast(
        "CursorResult[Any]",
        session.execute(
            delete(ConsumedRefreshToken).where(ConsumedRefreshToken.device_session_id.in_(beendet))
        ),
    )
    return int(ergebnis.rowcount or 0)
