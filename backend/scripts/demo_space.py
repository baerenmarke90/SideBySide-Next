"""Explicit create/reset entrypoint for the canonical development demo Space."""

from __future__ import annotations

import argparse
import os
from datetime import date

from sidebyside.config import get_settings
from sidebyside.db.session import unit_of_work
from sidebyside.demo import create_demo_space, reset_demo_space

LEA_PASSWORD_ENV = "SBS_DEMO_LEA_PASSWORD"
ALEX_PASSWORD_ENV = "SBS_DEMO_ALEX_PASSWORD"


def _reference_date(raw: str | None) -> date:
    if raw is None:
        return date.today()
    try:
        return date.fromisoformat(raw)
    except ValueError as error:
        raise SystemExit("--reference-date must use YYYY-MM-DD.") from error


def _required_secret(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} must be supplied explicitly for demo creation.")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or reset the canonical SideBySide demo Space."
    )
    parser.add_argument(
        "action",
        choices=("create", "reset"),
        help="create is idempotent; reset replaces only the verified demo Space",
    )
    parser.add_argument(
        "--reference-date",
        help="scenario reference date (YYYY-MM-DD); defaults to today's local date",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    settings = get_settings()
    reference_date = _reference_date(args.reference_date)

    with unit_of_work() as session:
        if args.action == "create":
            result = create_demo_space(
                session,
                environment=settings.environment,
                lea_password=_required_secret(LEA_PASSWORD_ENV),
                alex_password=_required_secret(ALEX_PASSWORD_ENV),
                reference_date=reference_date,
            )
        else:
            result = reset_demo_space(
                session,
                environment=settings.environment,
                reference_date=reference_date,
            )

    state = "created" if result.created else "already present"
    print(
        f"Canonical demo Space {state}: space={result.space_id} "
        f"reference_date={result.reference_date.isoformat()}"
    )
    print("Demo identities: Lea Sommer and Alex Winter (passwords are never printed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
