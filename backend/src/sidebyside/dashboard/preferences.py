"""Registry and persistence for personal Dashboard presentation preferences."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from sidebyside.core.errors import NotFoundError
from sidebyside.core.ids import new_id
from sidebyside.dashboard.models import DashboardModulePreference


class DashboardModuleKey(StrEnum):
    """Stable internal product keys for registered Dashboard modules."""

    UPCOMING = "upcoming"


class DashboardPreferenceErrorCode:
    MODULE_NOT_FOUND = "DASHBOARD_MODULE_NOT_FOUND"


DashboardItemLimit = Literal[1, 2, 3]


@dataclass(frozen=True)
class DashboardModuleDefinition:
    key: DashboardModuleKey
    default_item_limit: DashboardItemLimit
    allowed_item_limits: frozenset[DashboardItemLimit]


@dataclass(frozen=True)
class DashboardModuleState:
    key: DashboardModuleKey
    item_limit: DashboardItemLimit


CATALOG: tuple[DashboardModuleDefinition, ...] = (
    DashboardModuleDefinition(
        key=DashboardModuleKey.UPCOMING,
        default_item_limit=1,
        allowed_item_limits=frozenset({1, 2, 3}),
    ),
)

_DEFINITIONS = {definition.key: definition for definition in CATALOG}


def module_definition(module_key: str) -> DashboardModuleDefinition:
    """Resolve a wire key through the typed registry or fail closed."""
    try:
        key = DashboardModuleKey(module_key)
    except ValueError as error:
        raise NotFoundError(
            "Dashboard module not found.",
            DashboardPreferenceErrorCode.MODULE_NOT_FOUND,
        ) from error
    definition = _DEFINITIONS.get(key)
    if definition is None:
        raise NotFoundError(
            "Dashboard module not found.",
            DashboardPreferenceErrorCode.MODULE_NOT_FOUND,
        )
    return definition


def read_module_preferences(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
) -> list[DashboardModuleState]:
    """Return effective preferences for every centrally registered module."""
    keys = [definition.key.value for definition in CATALOG]
    rows = session.execute(
        select(DashboardModulePreference).where(
            DashboardModulePreference.account_id == account_id,
            DashboardModulePreference.space_id == space_id,
            DashboardModulePreference.module_key.in_(keys),
        )
    ).scalars()
    overrides = {DashboardModuleKey(row.module_key): row.item_limit for row in rows}
    return [
        DashboardModuleState(
            key=definition.key,
            item_limit=(
                override
                if (override := overrides.get(definition.key)) in definition.allowed_item_limits
                else definition.default_item_limit
            ),
        )
        for definition in CATALOG
    ]


def set_module_item_limit(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
    module_key: str,
    item_limit: DashboardItemLimit,
) -> DashboardModuleState:
    """Persist one Account+Space override with a PostgreSQL-safe upsert."""
    definition = module_definition(module_key)
    if item_limit not in definition.allowed_item_limits:
        raise ValueError("item_limit must be validated at the API boundary")

    statement = (
        insert(DashboardModulePreference)
        .values(
            id=new_id(),
            account_id=account_id,
            space_id=space_id,
            module_key=definition.key.value,
            item_limit=item_limit,
        )
        .on_conflict_do_update(
            constraint="uq_dashboard_module_preferences_account_space_module",
            set_={"item_limit": item_limit, "updated_at": func.now()},
        )
        .returning(DashboardModulePreference.item_limit)
    )
    persisted_item_limit = session.execute(statement).scalar_one()
    assert persisted_item_limit is not None
    session.flush()
    return DashboardModuleState(
        key=definition.key,
        item_limit=cast(DashboardItemLimit, persisted_item_limit),
    )
