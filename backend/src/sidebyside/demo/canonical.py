"""The reserved identities the public demo must be able to recognize again.

The demo is a shared, publicly reachable deployment whose content is thrown
away and rebuilt on a timer. That only works while the two reserved Accounts
stay recognizable: create/ensure/reset resolve them by their reserved address
and a durable technical identity marker (`sidebyside.demo.models`), never by
`display_name`, because a demo it cannot identify is one it must not delete a
Space for. `display_name` is ordinary mutable presentation data -- a visitor
is explicitly allowed to change it, and reset restores it rather than relying
on it (#633).

Everything a visitor does inside the Space is therefore disposable by design.
The Account-global name they could still change while the demo is live between
resets is additionally protected here, not because the reset depends on it,
but so a persona is not visibly mislabeled to other visitors until the next
reset runs. It is protected here rather than by hiding a control in a client:
a visitor holds an ordinary bearer token and can call the API directly; UI
visibility is a representation of a server decision, never the decision
itself.

This module deliberately depends only on configuration and the identity models.
The services that must not corrupt a reserved identity can therefore import it
without importing the demo seeding service that imports them.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from sidebyside.config import Environment, get_settings
from sidebyside.core.errors import ForbiddenError
from sidebyside.identity.models import Account, AccountEmail

LEA_EMAIL = "demo-lea@sidebyside.invalid"
ALEX_EMAIL = "demo-alex@sidebyside.invalid"
LEA_NAME = "Lea Sommer"
ALEX_NAME = "Alex Winter"

RESERVED_IDENTITIES: Mapping[str, str] = MappingProxyType(
    {
        LEA_EMAIL: LEA_NAME,
        ALEX_EMAIL: ALEX_NAME,
    }
)
"""Reserved address to the canonical display name reset restores.

This is presentation data reset writes back, not an identity check: the
address is what the guard and the reset resolve accounts by. Adding a persona
in one place therefore cannot leave the other behind.
"""


class DemoPersona:
    """The two canonical demo personas, independent of any presentation data."""

    LEA = "LEA"
    ALEX = "ALEX"


RESERVED_PERSONAS: Mapping[str, str] = MappingProxyType(
    {
        LEA_EMAIL: DemoPersona.LEA,
        ALEX_EMAIL: DemoPersona.ALEX,
    }
)
"""Reserved address to the durable persona marker `sidebyside.demo.models` stores.

`display_name` and even the reserved address itself are things a visitor or an
operator could, in principle, cause to drift; the marker is the technical fact
create/ensure/reset ultimately trust once it has been established. See
`sidebyside.demo.service` for how it is adopted for an already-deployed demo
database that predates this marker.
"""


class DemoIsolationErrorCode:
    CANONICAL_IDENTITY_IMMUTABLE = "DEMO_CANONICAL_IDENTITY_IMMUTABLE"
    """An Account-global mutation the demo reset could not reconstruct.

    The personas and their names are part of the public demo contract: the
    entry page offers them by name. Naming them in the refusal therefore
    discloses nothing, and the code is the same whichever persona is signed in.
    """


def demo_deployment() -> bool:
    """Whether this deployment is the public demo.

    ``SBS_ENVIRONMENT=demo`` requires ``SBS_DEMO_MODE=true``, and ordinary
    production rejects it, but both are read here so a deployment that enables
    only demo mode is still treated as a demo.
    """
    settings = get_settings()
    return settings.environment is Environment.DEMO or settings.demo_mode


def is_canonical_reserved_account(session: Session, account: Account) -> bool:
    """Whether the reset resolves this Account as one of its reserved personas.

    Membership is decided by the reserved address rather than by the current
    display name. Deciding it by the name would make the guard useless exactly
    once the name had already drifted.
    """
    return bool(
        session.execute(
            select(
                exists().where(
                    AccountEmail.account_id == account.id,
                    AccountEmail.email.in_(tuple(RESERVED_IDENTITIES)),
                )
            )
        ).scalar_one()
    )


def ensure_account_identity_mutable(session: Session, account: Account) -> None:
    """Refuse an Account-global mutation the demo reset cannot reconstruct.

    Callers decide which of their mutations is reset-critical, because that
    depends on what the reset rebuilds; this only answers whether the Account
    is one whose global identity the reset depends on. Space and product
    content stay mutable, since the reset replaces the Space wholesale.

    Outside a demo deployment nothing is refused. The reserved accounts do not
    exist in production, and elsewhere the reset's own fail-closed validation
    remains the operator-facing protection.
    """
    if not demo_deployment():
        return
    if not is_canonical_reserved_account(session, account):
        return
    raise ForbiddenError(
        "The demo personas keep their name so the demo can be reset. "
        "Everything inside the demo Space can still be changed.",
        DemoIsolationErrorCode.CANONICAL_IDENTITY_IMMUTABLE,
    )
