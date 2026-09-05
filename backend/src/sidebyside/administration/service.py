"""Application service for registration and maintenance administration."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from sidebyside.administration.models import (
    AdministrationAction,
    AdministrationSetting,
    InstanceAdministrationActionEvent,
    InstanceAdministrationEvent,
    InstanceAdministrationSettings,
)
from sidebyside.core.errors import ErrorCode, ForbiddenError, ServiceUnavailableError


@dataclass(frozen=True, slots=True)
class InstanceAccessState:
    """Stored and effective public access state."""

    registration_enabled: bool
    maintenance_mode: bool

    @property
    def effective_registration_enabled(self) -> bool:
        return self.registration_enabled and not self.maintenance_mode


def get_settings(session: Session, *, for_update: bool = False) -> InstanceAdministrationSettings:
    """Return the singleton settings row, creating safe defaults if necessary."""
    statement = select(InstanceAdministrationSettings).where(
        InstanceAdministrationSettings.singleton_key == 1
    )
    if for_update:
        statement = statement.with_for_update()
    settings = session.execute(statement).scalar_one_or_none()
    if settings is None:
        # SELECT ... FOR UPDATE cannot lock a row that does not exist. Use the
        # migration-compatible PostgreSQL upsert so concurrent first requests
        # cannot both create the singleton and turn a normal race into a 500.
        session.execute(
            insert(InstanceAdministrationSettings)
            .values(
                singleton_key=1,
                registration_enabled=True,
                maintenance_mode=False,
                version=1,
            )
            .on_conflict_do_nothing(index_elements=[InstanceAdministrationSettings.singleton_key])
        )
        settings = session.execute(statement).scalar_one()
    return settings


def get_access_state(session: Session) -> InstanceAccessState:
    settings = get_settings(session)
    return InstanceAccessState(
        registration_enabled=settings.registration_enabled,
        maintenance_mode=settings.maintenance_mode,
    )


def ensure_normal_operation(session: Session) -> None:
    """Reject ordinary product traffic while instance maintenance is active."""
    if get_access_state(session).maintenance_mode:
        raise ServiceUnavailableError(
            "SideBySide is temporarily unavailable for maintenance.",
            ErrorCode.MAINTENANCE_MODE,
        )


def ensure_new_account_registration_allowed(session: Session) -> None:
    """Reject creation of a new non-bootstrap account when policy disallows it."""
    state = get_access_state(session)
    if state.maintenance_mode:
        raise ServiceUnavailableError(
            "SideBySide is temporarily unavailable for maintenance.",
            ErrorCode.MAINTENANCE_MODE,
        )
    if not state.registration_enabled:
        raise ForbiddenError(
            "New account registration is disabled by the administrator.",
            ErrorCode.REGISTRATION_DISABLED,
        )


def update_setting(
    session: Session,
    *,
    actor_id: UUID,
    setting: AdministrationSetting,
    enabled: bool,
) -> InstanceAdministrationSettings:
    """Change one privileged setting and audit actual state transitions."""
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


def record_action(
    session: Session,
    *,
    actor_id: UUID | None,
    action: AdministrationAction,
    target_account_id: UUID | None = None,
    target_space_id: UUID | None = None,
    effect_count: int | None = None,
) -> InstanceAdministrationActionEvent:
    """Record one privileged Account/Space operation without storing user payloads."""
    event = InstanceAdministrationActionEvent(
        actor_id=actor_id,
        target_account_id=target_account_id,
        target_space_id=target_space_id,
        action=action.value,
        effect_count=effect_count,
    )
    session.add(event)
    session.flush()
    return event


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


def recent_action_events(
    session: Session, *, limit: int = 50
) -> list[InstanceAdministrationActionEvent]:
    return list(
        session.execute(
            select(InstanceAdministrationActionEvent)
            .order_by(InstanceAdministrationActionEvent.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
