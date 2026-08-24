"""Passwortlose Anmeldung, Adressverifikation und Account Recovery.

Drei Ablaeufe, die sich aehneln und trotzdem getrennt bleiben: jeder hat
seine eigene Tabelle, seine eigene Frist und seinen eigenen Endpunkt. Ein
Token aus dem einen kann damit im anderen nicht gelten - nicht, weil eine
Pruefung das verhindert, sondern weil er dort gar nicht gesucht wird.

Nach aussen sind sie einsilbig. Wer eine Adresse eingibt, erfaehrt nicht,
ob es sie gibt: die Antwort ist immer dieselbe. Sonst waere der
Anforderungs-Endpunkt ein bequemer Weg, Konten aufzuzaehlen.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth import action_tokens, passwords, rate_limit, sessions
from sidebyside.auth.sessions import IssuedTokens
from sidebyside.config import get_settings
from sidebyside.core.clock import now
from sidebyside.core.errors import ValidationError
from sidebyside.identity import service as accounts
from sidebyside.identity.models import (
    Account,
    AccountEmail,
    AccountRecoveryToken,
    MagicLinkToken,
)
from sidebyside.mail import MailMessage, MailSender, MailTransportError

log = logging.getLogger(__name__)

ACTION_MAGIC_LINK = "magic_link"
ACTION_EMAIL_VERIFICATION = "email_verification"
ACTION_RECOVERY = "account_recovery"


@dataclass(frozen=True)
class SignedIn:
    account: Account
    tokens: IssuedTokens


def _link(pfad: str, token: str) -> str:
    """Die Adresse, die in der Mail steht.

    Die Basis kommt aus der Konfiguration und nicht aus einem
    Request-Header: ein gefaelschter Host-Header wuerde den Link sonst auf
    einen fremden Server umbiegen, und der Empfaenger uebergaebe seinen
    Token dorthin.
    """
    basis = get_settings().public_base_url.rstrip("/")
    return f"{basis}/{pfad.lstrip('/')}?token={quote(token)}"


def _zustellen(mail: MailSender, nachricht: MailMessage) -> None:
    """Versenden, ohne dass ein Zustellfehler zur Auskunft wird.

    Ein Fehler beim Mailserver darf die Antwort nicht veraendern - sonst
    unterschiede sie sich zwischen bekannter und unbekannter Adresse. Er
    wird protokolliert, ohne Inhalt und ohne Token.
    """
    try:
        mail.send(nachricht)
    except MailTransportError:
        log.warning("could not deliver auth mail")


def _primary_email(session: Session, adresse: str) -> AccountEmail | None:
    return session.execute(
        select(AccountEmail).where(AccountEmail.email == adresse)
    ).scalar_one_or_none()


def _revoke_open(
    session: Session, tokens: list[MagicLinkToken] | list[AccountRecoveryToken]
) -> None:
    """Aeltere offene Tokens desselben Ablaufs entwerten.

    Es soll immer nur der zuletzt angeforderte Link gelten. Sonst haeufen
    sich gueltige Anmeldenachweise in fremden Postfaechern an, etwa nach
    einer Adressuebernahme.
    """
    jetzt = now()
    for token in tokens:
        if token.is_open(jetzt):
            token.revoked_at = jetzt
    session.flush()


def request_magic_link(session: Session, *, email: str, mail: MailSender) -> None:
    """Einen passwortlosen Anmeldelink anfordern.

    Kehrt immer wortlos zurueck. Ob eine Mail entstanden ist, steht nicht
    in der Antwort.
    """
    adresse = accounts.normalize_email(email)
    rate_limit.check(session, ACTION_MAGIC_LINK, adresse, rate_limit.MAGIC_LINK)
    rate_limit.record_attempt(session, ACTION_MAGIC_LINK, adresse)

    eintrag = _primary_email(session, adresse)
    if eintrag is None:
        return
    konto = session.get(Account, eintrag.account_id)
    if konto is None or not konto.is_active:
        return

    offen = list(
        session.execute(select(MagicLinkToken).where(MagicLinkToken.account_email_id == eintrag.id))
        .scalars()
        .all()
    )
    _revoke_open(session, offen)

    _, ausgestellt = action_tokens.issue_magic_link(session, eintrag.id)
    _zustellen(
        mail,
        MailMessage(
            to=adresse,
            subject="Dein Anmeldelink fuer SideBySide",
            body=(
                "Hier ist dein Anmeldelink:\n\n"
                f"{_link('auth/magic-link', ausgestellt.token)}\n\n"
                "Er gilt 15 Minuten und genau einmal.\n\n"
                "Wenn du ihn nicht angefordert hast, kannst du diese "
                "Nachricht ignorieren."
            ),
        ),
    )


def consume_magic_link(
    session: Session, *, token: str, device_name: str = "", platform: str = ""
) -> SignedIn:
    """Den Anmeldelink einloesen.

    Der eingeloeste Link belegt zugleich, dass die Adresse dem Empfaenger
    gehoert - sie gilt danach als verifiziert. Ein zweiter Weg dafuer
    waere eine zweite Gelegenheit, es zu vergessen.
    """
    modell = action_tokens.consume_magic_link(session, token)
    eintrag = session.get(AccountEmail, modell.account_email_id)
    konto = session.get(Account, eintrag.account_id) if eintrag is not None else None
    if eintrag is None or konto is None or not konto.is_active:
        raise ValidationError(
            "This authentication token is no longer valid.",
            action_tokens.ActionTokenErrorCode.INVALID,
        )

    if eintrag.verified_at is None:
        eintrag.verified_at = now()

    rate_limit.clear(session, ACTION_MAGIC_LINK, eintrag.email)
    _, ausgestellt = sessions.start_session(
        session, konto, device_name=device_name, platform=platform
    )
    session.flush()
    return SignedIn(account=konto, tokens=ausgestellt)


def request_email_verification(session: Session, account: Account, *, mail: MailSender) -> None:
    """Die Bestaetigung der eigenen Adresse anfordern.

    Anders als die beiden anderen Abläufe setzt dieser eine bestehende
    Anmeldung voraus: er sagt niemandem etwas, was er nicht schon weiss.
    """
    eintrag = session.execute(
        select(AccountEmail).where(
            AccountEmail.account_id == account.id,
            AccountEmail.is_primary.is_(True),
        )
    ).scalar_one_or_none()
    if eintrag is None or eintrag.verified_at is not None:
        return

    rate_limit.check(session, ACTION_EMAIL_VERIFICATION, eintrag.email, rate_limit.MAGIC_LINK)
    rate_limit.record_attempt(session, ACTION_EMAIL_VERIFICATION, eintrag.email)

    _, ausgestellt = action_tokens.issue_email_verification(session, eintrag.id)
    _zustellen(
        mail,
        MailMessage(
            to=eintrag.email,
            subject="Bestaetige deine E-Mail-Adresse",
            body=(
                "Bitte bestaetige deine Adresse:\n\n"
                f"{_link('auth/verify-email', ausgestellt.token)}\n\n"
                "Der Link gilt 24 Stunden und genau einmal."
            ),
        ),
    )


def confirm_email(session: Session, *, token: str) -> AccountEmail:
    """Die Adresse als bestaetigt vermerken.

    Bewusst ohne Sitzung: der Link wird oft in einem anderen Programm
    geoeffnet als dem, in dem die Anmeldung liegt.
    """
    modell = action_tokens.consume_email_verification(session, token)
    eintrag = session.get(AccountEmail, modell.account_email_id)
    if eintrag is None:
        raise ValidationError(
            "This authentication token is no longer valid.",
            action_tokens.ActionTokenErrorCode.INVALID,
        )
    if eintrag.verified_at is None:
        eintrag.verified_at = now()
    session.flush()
    return eintrag


def request_recovery(session: Session, *, email: str, mail: MailSender) -> None:
    """Die Wiederherstellung eines Passworts anfordern.

    Nur fuer Accounts, die ueberhaupt ein Passwort haben. Wer sich
    ausschliesslich ueber einen externen Anbieter anmeldet, bekommt hier
    keines eingerichtet - das waere ein zusaetzlicher Anmeldeweg, den
    niemand verlangt hat.
    """
    adresse = accounts.normalize_email(email)
    rate_limit.check(session, ACTION_RECOVERY, adresse, rate_limit.MAGIC_LINK)
    rate_limit.record_attempt(session, ACTION_RECOVERY, adresse)

    eintrag = _primary_email(session, adresse)
    konto = session.get(Account, eintrag.account_id) if eintrag is not None else None
    if konto is None or not konto.is_active:
        return
    if accounts.local_identity(session, konto) is None:
        return

    offen = list(
        session.execute(
            select(AccountRecoveryToken).where(AccountRecoveryToken.account_id == konto.id)
        )
        .scalars()
        .all()
    )
    _revoke_open(session, offen)

    _, ausgestellt = action_tokens.issue_account_recovery(session, konto.id)
    _zustellen(
        mail,
        MailMessage(
            to=adresse,
            subject="Passwort zuruecksetzen",
            body=(
                "Mit diesem Link kannst du ein neues Passwort setzen:\n\n"
                f"{_link('auth/recovery', ausgestellt.token)}\n\n"
                "Er gilt 30 Minuten und genau einmal. Danach sind alle "
                "angemeldeten Geraete abgemeldet.\n\n"
                "Wenn du ihn nicht angefordert hast, aendert sich nichts."
            ),
        ),
    )


def consume_recovery(
    session: Session,
    *,
    token: str,
    new_password: str,
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    """Ein neues Passwort setzen und alle Sitzungen beenden.

    Alle: wer ein Passwort zuruecksetzt, vermutet oft einen fremden
    Zugriff. Danach beginnt genau eine neue Sitzung - die auf diesem
    Geraet.
    """
    passwords.validate(new_password)

    modell = action_tokens.consume_account_recovery(session, token)
    konto = session.get(Account, modell.account_id)
    identitaet = accounts.local_identity(session, konto) if konto is not None else None
    if konto is None or not konto.is_active or identitaet is None:
        raise ValidationError(
            "This authentication token is no longer valid.",
            action_tokens.ActionTokenErrorCode.INVALID,
        )

    identitaet.secret_hash = passwords.hash_password(new_password)
    sessions.revoke_all(session, konto)

    _, ausgestellt = sessions.start_session(
        session, konto, device_name=device_name, platform=platform
    )
    session.flush()
    return SignedIn(account=konto, tokens=ausgestellt)
