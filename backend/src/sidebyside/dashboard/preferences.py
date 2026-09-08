"""Catalog and persistence service for personal Dashboard module visibility."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from sidebyside.core.ids import new_id
from sidebyside.dashboard.models import DashboardModulePreference


class DashboardModuleKey(StrEnum):
    """Stable product keys for modules registered with Dashboard settings."""

    SHARED_STORY_SUMMARY = "SHARED_STORY_SUMMARY"


@dataclass(frozen=True)
class DashboardModuleDefinition:
    key: DashboardModuleKey
    default_visible: bool


@dataclass(frozen=True)
class DashboardModuleState:
    key: DashboardModuleKey
    visible: bool


CATALOG: tuple[DashboardModuleDefinition, ...] = (
    DashboardModuleDefinition(
        key=DashboardModuleKey.SHARED_STORY_SUMMARY,
        default_visible=True,
    ),
)

_DEFINITIONS = {definition.key: definition for definition in CATALOG}


def read_module_preferences(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
) -> list[DashboardModuleState]:
    """Return the effective visibility of every centrally registered module."""
    keys = [definition.key.value for definition in CATALOG]
    rows = session.execute(
        select(DashboardModulePreference).where(
            DashboardModulePreference.account_id == account_id,
            DashboardModulePreference.space_id == space_id,
            DashboardModulePreference.module_key.in_(keys),
        )
    ).scalars()
    overrides = {DashboardModuleKey(row.module_key): row.visible for row in rows}
    return [
        DashboardModuleState(
            key=definition.key,
            visible=overrides.get(definition.key, definition.default_visible),
        )
        for definition in CATALOG
    ]


def set_module_visibility(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
    module_key: DashboardModuleKey,
    visible: bool,
) -> DashboardModuleState:
    """Persist one account+Space override using a race-safe PostgreSQL upsert."""
    definition = _DEFINITIONS[module_key]
    statement = (
        insert(DashboardModulePreference)
        .values(
            id=new_id(),
            account_id=account_id,
            space_id=space_id,
            module_key=module_key.value,
            visible=visible,
        )
        .on_conflict_do_update(
            constraint="uq_dashboard_module_preferences_account_space_module",
            set_={"visible": visible, "updated_at": func.now()},
        )
        .returning(DashboardModulePreference.visible)
    )
    persisted_visible = bool(session.execute(statement).scalar_one())
    session.flush()
    return DashboardModuleState(
        key=definition.key,
        visible=persisted_visible,
    )
