"""Provider-neutral, content-minimized M4-B push delivery."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from sidebyside.core import clock
from sidebyside.engagement.models import (
    Notification,
    PushDelivery,
    PushDeliveryStatus,
    PushEndpoint,
)
from sidebyside.jobs import queue
from sidebyside.jobs.errors import RetryableJobError
from sidebyside.jobs.worker import registry
from sidebyside.relationship.models import Membership, MembershipStatus

JOB_KIND = "push-delivery"
GENERIC_PRESENTATION_KEY = "notification.generic"
MAX_PUSH_ATTEMPTS = 5
_ERROR_CODE = re.compile(r"[^A-Z0-9_-]+")


@dataclass(frozen=True)
class PushSendResult:
    provider_message_id: str | None = None


class PushProvider(Protocol):
    def send(
        self,
        *,
        idempotency_key: str,
        endpoint: str,
        notification_reference: dict[str, str],
        generic_presentation_key: str,
    ) -> PushSendResult: ...


class PushProviderError(Exception):
    """Provider failure represented only by a bounded technical code."""

    def __init__(self, code: str) -> None:
        self.code = sanitize_error_code(code)
        super().__init__(self.code)


class PushProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, PushProvider] = {}

    def register(self, provider_key: str, provider: PushProvider) -> None:
        key = provider_key.strip()
        if not key:
            raise ValueError("provider_key must not be blank")
        self._providers[key] = provider

    def get(self, provider_key: str) -> PushProvider | None:
        return self._providers.get(provider_key)

    def clear(self) -> None:
        self._providers.clear()


providers = PushProviderRegistry()


def register_handlers() -> None:
    """Register the existing Job Queue handler exactly once per worker process."""
    if registry.get(JOB_KIND) is None:
        registry.register(JOB_KIND, handle_delivery)


def register_endpoint(
    session: Session,
    *,
    account_id: UUID,
    provider_key: str,
    endpoint_value: str,
) -> PushEndpoint:
    """Create/reactivate one technical endpoint without exposing it publicly."""
    provider = provider_key.strip()
    endpoint = endpoint_value.strip()
    if not provider or not endpoint:
        raise ValueError("push endpoint and provider must not be blank")

    fingerprint = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()
    statement = (
        postgresql.insert(PushEndpoint)
        .values(
            account_id=account_id,
            provider_key=provider,
            endpoint_value=endpoint,
            fingerprint=fingerprint,
            disabled_at=None,
        )
        .on_conflict_do_update(
            index_elements=["account_id", "provider_key", "fingerprint"],
            set_={"endpoint_value": endpoint, "disabled_at": None},
        )
        .returning(PushEndpoint.id)
    )
    endpoint_id = session.execute(statement).scalar_one()
    return session.get(PushEndpoint, endpoint_id)  # type: ignore[return-value]


def ensure_deliveries_for_source_event(session: Session, source_event_id: UUID) -> None:
    """Create one logical delivery per active endpoint for projected Notifications."""
    notifications = session.execute(
        select(Notification).where(Notification.source_event_id == source_event_id)
    ).scalars()
    for notification in notifications:
        endpoints = session.execute(
            select(PushEndpoint).where(
                PushEndpoint.account_id == notification.recipient_account_id,
                PushEndpoint.disabled_at.is_(None),
            )
        ).scalars()
        for endpoint in endpoints:
            statement = (
                postgresql.insert(PushDelivery)
                .values(
                    notification_id=notification.id,
                    push_endpoint_id=endpoint.id,
                    provider_key=endpoint.provider_key,
                    status=PushDeliveryStatus.PENDING.value,
                    attempts=0,
                )
                .on_conflict_do_nothing(
                    index_elements=["notification_id", "push_endpoint_id"]
                )
                .returning(PushDelivery.id)
            )
            delivery_id = session.execute(statement).scalar_one_or_none()
            if delivery_id is not None:
                queue.enqueue(
                    session,
                    JOB_KIND,
                    {"deliveryId": str(delivery_id)},
                    max_attempts=MAX_PUSH_ATTEMPTS,
                )


def handle_delivery(session: Session, payload: dict[str, Any]) -> None:
    """Deliver one Notification without carrying relationship plaintext."""
    raw_id = payload.get("deliveryId")
    if not isinstance(raw_id, str):
        return
    try:
        delivery_id = UUID(raw_id)
    except ValueError:
        return

    delivery = session.execute(
        select(PushDelivery).where(PushDelivery.id == delivery_id).with_for_update()
    ).scalar_one_or_none()
    if delivery is None or delivery.status in {
        PushDeliveryStatus.SUCCEEDED.value,
        PushDeliveryStatus.FAILED.value,
        PushDeliveryStatus.UNAVAILABLE.value,
    }:
        return

    notification = session.get(Notification, delivery.notification_id)
    endpoint = session.get(PushEndpoint, delivery.push_endpoint_id)
    if (
        notification is None
        or endpoint is None
        or endpoint.disabled_at is not None
        or endpoint.account_id != notification.recipient_account_id
    ):
        _finish_unavailable(delivery)
        return

    active_membership = session.execute(
        select(Membership.id).where(
            Membership.space_id == notification.space_id,
            Membership.account_id == notification.recipient_account_id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
    ).scalar_one_or_none()
    if active_membership is None:
        _finish_unavailable(delivery)
        return

    provider = providers.get(delivery.provider_key)
    if provider is None:
        _finish_unavailable(delivery)
        return

    delivery.attempts += 1
    try:
        result = provider.send(
            idempotency_key=f"{notification.id}:{endpoint.id}",
            endpoint=endpoint.endpoint_value,
            notification_reference={
                "id": str(notification.id),
                "kind": notification.kind,
            },
            generic_presentation_key=GENERIC_PRESENTATION_KEY,
        )
    except PushProviderError as exc:
        _record_failure(delivery, exc.code)
        if delivery.attempts < MAX_PUSH_ATTEMPTS:
            raise RetryableJobError(exc.code) from exc
        return
    except Exception as exc:
        code = "PROVIDER_ERROR"
        _record_failure(delivery, code)
        if delivery.attempts < MAX_PUSH_ATTEMPTS:
            raise RetryableJobError(code) from exc
        return

    delivery.status = PushDeliveryStatus.SUCCEEDED.value
    delivery.last_error_code = None
    delivery.provider_message_id = bounded_identifier(result.provider_message_id)
    delivery.finished_at = clock.now()


def sanitize_error_code(value: str) -> str:
    normalized = _ERROR_CODE.sub("_", value.strip().upper()).strip("_")
    return (normalized or "PROVIDER_ERROR")[:64]


def bounded_identifier(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = "".join(character for character in value if character.isprintable()).strip()
    return cleaned[:256] or None


def _record_failure(delivery: PushDelivery, code: str) -> None:
    delivery.last_error_code = sanitize_error_code(code)
    if delivery.attempts >= MAX_PUSH_ATTEMPTS:
        delivery.status = PushDeliveryStatus.FAILED.value
        delivery.finished_at = clock.now()
    else:
        delivery.status = PushDeliveryStatus.RETRYING.value


def _finish_unavailable(delivery: PushDelivery) -> None:
    delivery.status = PushDeliveryStatus.UNAVAILABLE.value
    delivery.last_error_code = "PUSH_NOT_CONFIGURED"
    delivery.finished_at = clock.now()
