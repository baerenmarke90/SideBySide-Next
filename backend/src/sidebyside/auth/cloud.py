"""Passwordless sign-in, address verification, and account recovery.

Three flows that look similar but deliberately remain separate: each has its
own table, lifetime, and endpoint. A token from one cannot be accepted by
another because that other flow never looks it up.

Externally the request paths remain terse. A caller who submits an address must
not learn whether it exists; otherwise the request endpoint would be a simple
account-enumeration oracle.
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


def _link(path: str, token: str) -> str:
    """Build the address placed into authentication mail.

    The base comes from configuration rather than a request header. Otherwise a
    forged Host header could redirect the link to an attacker-controlled server
    and cause the recipient to hand over the token there.
    """
    base = get_settings().public_base_url.rstrip("/")
    return f"{base}/{path.lstrip('/')}?token={quote(token)}"


def _deliver(mail: MailSender, message: MailMessage) -> None:
    """Deliver mail without turning transport failure into an oracle.

    A mail-server failure must not change the response, because that could make
    known and unknown addresses distinguishable. Log the transport failure
    without message content or tokens.
    """
    try:
        mail.send(message)
    except MailTransportError:
        log.warning("could not deliver auth mail")


def _primary_email(session: Session, address: str) -> AccountEmail | None:
    return session.execute(
        select(AccountEmail).where(AccountEmail.email == address)
    ).scalar_one_or_none()


def _revoke_open(
    session: Session, tokens: list[MagicLinkToken] | list[AccountRecoveryToken]
) -> None:
    """Revoke older open tokens for the same flow.

    Only the most recently requested link should remain valid. Otherwise valid
    authentication proofs accumulate in mailboxes outside the application,
    including after an address changes hands.
    """
    current_time = now()
    for token in tokens:
        if token.is_open(current_time):
            token.revoked_at = current_time
    session.flush()


def request_magic_link(session: Session, *, email: str, mail: MailSender) -> None:
    """Request a passwordless sign-in link.

    The response never reveals whether mail was created.
    """
    address = accounts.normalize_email(email)
    rate_limit.check(session, ACTION_MAGIC_LINK, address, rate_limit.MAGIC_LINK)
    rate_limit.record_attempt(session, ACTION_MAGIC_LINK, address)

    email_record = _primary_email(session, address)
    if email_record is None:
        return
    account = session.get(Account, email_record.account_id)
    if account is None or not account.is_active:
        return

    open_tokens = list(
        session.execute(
            select(MagicLinkToken).where(MagicLinkToken.account_email_id == email_record.id)
        )
        .scalars()
        .all()
    )
    _revoke_open(session, open_tokens)

    _, issued = action_tokens.issue_magic_link(session, email_record.id)
    _deliver(
        mail,
        MailMessage(
            to=address,
            subject="Dein Anmeldelink fuer SideBySide",
            body=(
                "Hier ist dein Anmeldelink:\n\n"
                f"{_link('auth/magic-link', issued.token)}\n\n"
                "Er gilt 15 Minuten und genau einmal.\n\n"
                "Wenn du ihn nicht angefordert hast, kannst du diese "
                "Nachricht ignorieren."
            ),
        ),
    )


def consume_magic_link(
    session: Session, *, token: str, device_name: str = "", platform: str = ""
) -> SignedIn:
    """Consume a sign-in link.

    A consumed link also proves that the recipient controls the address, so it
    becomes verified. A separate verification step would create another place
    where that fact could be forgotten.
    """
    model = action_tokens.consume_magic_link(session, token)
    email_record = session.get(AccountEmail, model.account_email_id)
    account = session.get(Account, email_record.account_id) if email_record is not None else None
    if email_record is None or account is None or not account.is_active:
        raise ValidationError(
            "This authentication token is no longer valid.",
            action_tokens.ActionTokenErrorCode.INVALID,
        )

    if email_record.verified_at is None:
        email_record.verified_at = now()

    rate_limit.clear(session, ACTION_MAGIC_LINK, email_record.email)
    _, issued = sessions.start_session(session, account, device_name=device_name, platform=platform)
    session.flush()
    return SignedIn(account=account, tokens=issued)


def request_email_verification(session: Session, account: Account, *, mail: MailSender) -> None:
    """Request verification of the account's own address.

    Unlike the other two flows, this requires an existing authenticated account
    and therefore reveals nothing the caller does not already know.
    """
    email_record = session.execute(
        select(AccountEmail).where(
            AccountEmail.account_id == account.id,
            AccountEmail.is_primary.is_(True),
        )
    ).scalar_one_or_none()
    if email_record is None or email_record.verified_at is not None:
        return

    rate_limit.check(session, ACTION_EMAIL_VERIFICATION, email_record.email, rate_limit.MAGIC_LINK)
    rate_limit.record_attempt(session, ACTION_EMAIL_VERIFICATION, email_record.email)

    _, issued = action_tokens.issue_email_verification(session, email_record.id)
    _deliver(
        mail,
        MailMessage(
            to=email_record.email,
            subject="Bestaetige deine E-Mail-Adresse",
            body=(
                "Bitte bestaetige deine Adresse:\n\n"
                f"{_link('auth/verify-email', issued.token)}\n\n"
                "Der Link gilt 24 Stunden und genau einmal."
            ),
        ),
    )


def confirm_email(session: Session, *, token: str) -> AccountEmail:
    """Mark the address as verified.

    This deliberately requires no session because the link is often opened in a
    different program from the one holding the sign-in session.
    """
    model = action_tokens.consume_email_verification(session, token)
    email_record = session.get(AccountEmail, model.account_email_id)
    if email_record is None:
        raise ValidationError(
            "This authentication token is no longer valid.",
            action_tokens.ActionTokenErrorCode.INVALID,
        )
    if email_record.verified_at is None:
        email_record.verified_at = now()
    session.flush()
    return email_record


def request_recovery(session: Session, *, email: str, mail: MailSender) -> None:
    """Request password recovery.

    Only accounts that already have a local password are eligible. An account
    that signs in exclusively through an external provider must not silently
    gain an additional authentication method here.
    """
    address = accounts.normalize_email(email)
    rate_limit.check(session, ACTION_RECOVERY, address, rate_limit.MAGIC_LINK)
    rate_limit.record_attempt(session, ACTION_RECOVERY, address)

    email_record = _primary_email(session, address)
    account = session.get(Account, email_record.account_id) if email_record is not None else None
    if account is None or not account.is_active:
        return
    if accounts.local_identity(session, account) is None:
        return

    open_tokens = list(
        session.execute(
            select(AccountRecoveryToken).where(AccountRecoveryToken.account_id == account.id)
        )
        .scalars()
        .all()
    )
    _revoke_open(session, open_tokens)

    _, issued = action_tokens.issue_account_recovery(session, account.id)
    _deliver(
        mail,
        MailMessage(
            to=address,
            subject="Passwort zuruecksetzen",
            body=(
                "Mit diesem Link kannst du ein neues Passwort setzen:\n\n"
                f"{_link('auth/recovery', issued.token)}\n\n"
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
    """Set a new password and revoke all sessions.

    Password recovery commonly follows suspected unauthorized access. Every old
    session is therefore revoked and exactly one new session begins on the
    current device.
    """
    passwords.validate(new_password)

    model = action_tokens.consume_account_recovery(session, token)
    account = session.get(Account, model.account_id)
    identity = accounts.local_identity(session, account) if account is not None else None
    if account is None or not account.is_active or identity is None:
        raise ValidationError(
            "This authentication token is no longer valid.",
            action_tokens.ActionTokenErrorCode.INVALID,
        )

    identity.secret_hash = passwords.hash_password(new_password)
    sessions.revoke_all(session, account)

    _, issued = sessions.start_session(session, account, device_name=device_name, platform=platform)
    session.flush()
    return SignedIn(account=account, tokens=issued)
