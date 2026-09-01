"""Application service for registration and maintenance administration."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.administration.models import (
    AdministrationSetting,
    InstanceAdministrationEvent,
    InstanceAdministrationSettings,
)


@dataclass(frozen=True, slots=True)
class InstanceAccessState:
    """Stored and effective public access state."""

    registration_enabled: bool
    maintenance_mode: bool

    @property
    def effective_registration_enabled(self) -> bool:
        return self.registration_enabled and not self.maintenance_mode


def get_settings(session: Session, *, for_update: bool = False) -> InstanceAdministrationSettings:
    """Return the singleton settings row, creating the safe default for fresh test DBs."""
    statement = select(InstanceAdministrationSettings).where(
        InstanceAdministrationSettings.singleton_key == 1
    )
    if for_update:
        statement = statement.with_for_update()
    settings = session.execute(statement).scalar_one_or_none()
    if settings is None:
        settings = InstanceAdministrationSettings(
            singleton_key=1,
            registration_enabled=True,
            maintenance_mode=False,
        )
        session.add(settings)
        session.flush()
    return settings


def get_access_state(session: Session) -> InstanceAccessState:
    settings = get_settings(session)
    return InstanceAccessState(
        registration_enabled=settings.registration_enabled,
        maintenance_mode=settings.maintenance_mode,
    )


def update_setting(
    session: Session,
    *,
    actor_id: UUID,
    setting: AdministrationSetting,
    enabled: bool,
) -> InstanceAdministrationSettings:
    """Change one privileged setting and append audit history on an actual mutation."""
    settings = get_settings(session, for_update=True)
    attribute = setting.value
    previous = bool(getattr(settings, attribute))
    if previous == enabled:
        return settings

    setattr(settings, attribute, enabled)
    session.add(
        InstanceAdministrationEvent(
            actor_id=actor_id,
            setting=setting.value,
            previous_value=previous,
            new_value=enabled,
        )
    )
    session.flush()
    return settings


def recent_events(session: Session, *, limit: int = 20) -> list[InstanceAdministrationEvent]:
    return list(
        session.execute(
            select(InstanceAdministrationEvent)
            .order_by(InstanceAdministrationEvent.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
