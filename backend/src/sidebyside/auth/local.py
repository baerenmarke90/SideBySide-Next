"""Registration and sign-in with a local password.

This is the self-hosted path. Cloud uses magic links and passkeys without a
password requirement; those are separate sign-in methods and do not change the
semantics here.

## Why registration requires an invitation

Open registration would be a security defect on a private couple instance:
anyone who knows the address could create an account. That alone would not grant
space membership, but an outsider would gain a foothold and could consume
sign-in attempt budgets.

The first account therefore requires a one-time secret bootstrap proof. Every
later registration requires a valid invitation.

Changing that policy must happen here deliberately and visibly.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from sidebyside.auth import bootstrap, passwords, rate_limit, sessions
from sidebyside.auth.sessions import IssuedTokens
from sidebyside.core.errors import ErrorCode, UnauthenticatedError, ValidationError
from sidebyside.identity import service as accounts
from sidebyside.identity.models import Account
from sidebyside.relationship import invitations
from sidebyside.relationship import service as spaces

ACTION_SIGN_IN = "sign_in"
ACTION_ACCEPT = "invitation_accept"


class AuthErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"


@dataclass(frozen=True)
class SignedIn:
    account: Account
    tokens: IssuedTokens


def register(
    session: Session,
    *,
    display_name: str,
    email: str,
    password: str,
    invitation_token: str | None = None,
    bootstrap_token: str | None = None,
    configured_bootstrap_token: str | None = None,
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    """Create an account and sign it in immediately.

    The first account requires the one-time bootstrap proof and receives its
    own space. Every later account joins through an invitation.
    """
    # Validate the password before creating the account. Otherwise a database
    # row could be created only for registration to fail afterward.
    passwords.validate(password)

    bootstrap_state = None
    if invitation_token:
        rate_limit.check(session, ACTION_ACCEPT, invitation_token, rate_limit.INVITATION_ACCEPT)
        rate_limit.record_attempt(session, ACTION_ACCEPT, invitation_token)
    else:
        bootstrap_state = bootstrap.claim(
            session,
            presented_token=bootstrap_token,
            configured_token=configured_bootstrap_token,
        )

    account = accounts.create_account(
        session,
        display_name=display_name,
        email=email,
        password_hash=passwords.hash_password(password),
    )

    if bootstrap_state is not None:
        spaces.create_space(session, account)
        bootstrap.complete(bootstrap_state, account)
    else:
        assert invitation_token is not None
        invitations.accept(session, invitation_token, account)
        rate_limit.clear(session, ACTION_ACCEPT, invitation_token)

    _, tokens = sessions.start_session(
        session, account, device_name=device_name, platform=platform
    )
    session.flush()
    return SignedIn(account=account, tokens=tokens)


def sign_in(
    session: Session,
    *,
    email: str,
    password: str,
    device_name: str = "",
    platform: str = "",
) -> SignedIn:
    """Sign in with a local password.

    Unknown address and wrong password produce the same response. Distinguishing
    them would reveal which addresses are registered and enable enumeration.
    """
    address = accounts.normalize_email(email)
    failed = UnauthenticatedError(
        "Email address or password is incorrect.", AuthErrorCode.INVALID_CREDENTIALS
    )

    # Check before the expensive password operation so it cannot be abused as
    # a compute-amplification path.
    rate_limit.check(session, ACTION_SIGN_IN, address, rate_limit.SIGN_IN)
    rate_limit.record_attempt(session, ACTION_SIGN_IN, address)

    account = accounts.find_by_email(session, address)
    identity = accounts.local_identity(session, account) if account else None

    # Perform one hash verification even without an account. Otherwise unknown
    # addresses would be measurably faster than wrong passwords and leak which
    # addresses are registered.
    password_hash = (
        identity.secret_hash
        if identity is not None and identity.secret_hash
        else passwords.DUMMY_HASH
    )
    matches = passwords.verify_password(password_hash, password)

    if account is None or identity is None or not matches:
        rate_limit.preserve_attempt_after_rollback(session, ACTION_SIGN_IN, address)
        raise failed
    if not account.is_active:
        rate_limit.preserve_attempt_after_rollback(session, ACTION_SIGN_IN, address)
        raise failed

    if passwords.needs_rehash(password_hash):
        identity.secret_hash = passwords.hash_password(password)

    rate_limit.clear(session, ACTION_SIGN_IN, address)

    _, tokens = sessions.start_session(
        session, account, device_name=device_name, platform=platform
    )
    session.flush()
    return SignedIn(account=account, tokens=tokens)


def change_password(session: Session, account: Account, *, current: str, new: str) -> None:
    """Change the local password.

    All other sessions are revoked. Password changes often follow suspected
    compromise, so another device must not remain signed in afterward.
    """
    identity = accounts.local_identity(session, account)
    if identity is None or not identity.secret_hash:
        raise ValidationError("This account has no password sign-in.", ErrorCode.VALIDATION_FAILED)
    if not passwords.verify_password(identity.secret_hash, current):
        raise UnauthenticatedError(
            "Email address or password is incorrect.", AuthErrorCode.INVALID_CREDENTIALS
        )

    identity.secret_hash = passwords.hash_password(new)
    sessions.revoke_all(session, account)
    session.flush()
