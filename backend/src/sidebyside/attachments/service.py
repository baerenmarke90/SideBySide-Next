"""Der Attachment-Lebenszyklus.

Ein erfolgreicher Providerupload ist nicht `READY`. Zwischen beiden liegt
die serverseitige Validierung, und sie entscheidet allein - genau deshalb
laeuft sie nicht im Requestpfad, sondern als Aufgabe in der vorhandenen
Warteschlange.

Der Statusautomat aus M2-D05 ist hier die einzige Wahrheit. Jeder Uebergang
prueft seinen Ausgangszustand; ein Aufruf zur falschen Zeit aendert nichts,
statt einen halben Schritt zu tun.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import BinaryIO
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.attachments import images
from sidebyside.attachments.limits import MediaRule, rule_for
from sidebyside.attachments.models import (
    Attachment,
    AttachmentPayload,
    AttachmentStatus,
    MediaType,
)
from sidebyside.authorization import (
    AuthorizationContext,
    PrivacyClass,
    require_readable,
    require_writable,
)
from sidebyside.core.clock import now
from sidebyside.core.errors import (
    ConflictError,
    ErrorCode,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from sidebyside.jobs import queue
from sidebyside.media import build_storage_key, get_media_store

log = logging.getLogger(__name__)

ATTACHMENT_VALIDATION = "attachment_validation"

BINDING_WINDOW = timedelta(minutes=60)
"""M2-D20: so lange darf ein READY Attachment ungebunden bleiben."""

ORIGINAL_VARIANT = "original"
THUMBNAIL_VARIANT = "thumbnail"

MAX_ORIGINAL_NAME = 255


@dataclass(frozen=True)
class ReadTarget:
    """Woraufhin ein Lesezugriff geprueft wird.

    `parent_type is None` bezeichnet den eigenen ungebundenen Upload im
    Bindungsfenster (M2-D24).
    """

    parent_type: str | None
    parent_id: UUID | None


def _flush(session: Session) -> None:
    try:
        session.flush()
    except StaleDataError as error:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        ) from error


def _not_ready() -> ConflictError:
    return ConflictError(
        "The attachment is not ready.",
        ErrorCode.ATTACHMENT_NOT_READY,
    )


def storage_key_for(attachment: Attachment, variant: str = ORIGINAL_VARIANT) -> str:
    return build_storage_key(attachment.space_id, attachment.id, variant)


def _require_rule(mime_type: str, media_type: MediaType) -> MediaRule:
    rule = rule_for(mime_type)
    if rule is None or rule.media_type is not media_type:
        raise UnsupportedMediaTypeError(
            "This media type is not accepted.",
            ErrorCode.ATTACHMENT_TYPE_NOT_ALLOWED,
        )
    if not rule.supported:
        # M2-D23: der Vertrag erlaubt den Typ, dieser Lieferstand nicht.
        # Fail-closed und mit demselben Code wie ein unbekannter Typ - der
        # Unterschied geht den Client nichts an.
        raise UnsupportedMediaTypeError(
            "This media type is not accepted.",
            ErrorCode.ATTACHMENT_TYPE_NOT_ALLOWED,
        )
    return rule


def create_upload(
    session: Session,
    context: AuthorizationContext,
    *,
    media_type: MediaType,
    original_name: str,
    expected_mime_type: str,
    expected_size: int,
) -> Attachment:
    """Einen Upload anmelden.

    Die Pruefung hier ist eine Vorabpruefung auf Clientangaben und ersetzt
    die spaetere Validierung am echten Objekt nicht. Sie erspart nur, eine
    aussichtslose Datei erst hochzuladen.
    """
    rule = _require_rule(expected_mime_type, media_type)

    name = original_name.strip()
    if not name or len(name) > MAX_ORIGINAL_NAME:
        raise ValidationError("An original name is required.", "ATTACHMENT_NAME_REQUIRED")
    if expected_size <= 0:
        raise ValidationError("An expected size is required.", "ATTACHMENT_SIZE_REQUIRED")
    if expected_size > rule.max_size:
        raise PayloadTooLargeError(
            "The attachment exceeds the size limit.",
            ErrorCode.ATTACHMENT_TOO_LARGE,
        )

    attachment = Attachment(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=PrivacyClass.OWNER_ONLY.value,
        status=AttachmentStatus.PENDING.value,
        media_type=media_type.value,
        declared_mime_type=rule.mime_type,
        declared_size=expected_size,
        payload=AttachmentPayload(original_name=name),
    )
    session.add(attachment)
    _flush(session)
    return attachment


def open_upload(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
) -> tuple[Attachment, MediaRule]:
    """Autorisieren und den Uploadplatz oeffnen - vor dem ersten Byte.

    Erst diese Pruefung, dann der Koerper. Umgekehrt entschiede ein
    beliebiger Absender darueber, wie viel der Server entgegennimmt, bevor
    ueberhaupt feststeht, ob er das darf.

    Ein erneuter Upload auf dasselbe PENDING/UPLOADING-Attachment ist
    erlaubt und ueberschreibt: ein abgebrochener Transfer soll keinen neuen
    Attachment-Datensatz erzwingen.
    """
    attachment = require_writable(session, Attachment, context, attachment_id)
    if attachment.status not in (
        AttachmentStatus.PENDING.value,
        AttachmentStatus.UPLOADING.value,
    ):
        raise ConflictError(
            "The upload target is not open.",
            ErrorCode.ATTACHMENT_NOT_READY,
        )
    rule = _require_rule(attachment.declared_mime_type, MediaType(attachment.media_type))
    return attachment, rule


def too_large() -> PayloadTooLargeError:
    return PayloadTooLargeError(
        "The attachment exceeds the size limit.",
        ErrorCode.ATTACHMENT_TOO_LARGE,
    )


def complete_upload(
    session: Session,
    attachment: Attachment,
    rule: MediaRule,
    data: bytes,
) -> Attachment:
    """Die entgegengenommenen Bytes ablegen.

    Die Groessengrenze ist beim Lesen bereits gezogen worden; hier wird sie
    noch einmal geprueft, damit kein anderer Aufrufer sie umgehen kann.
    """
    if len(data) > rule.max_size:
        raise too_large()
    get_media_store().put(storage_key_for(attachment), io.BytesIO(data), rule.mime_type)
    attachment.status = AttachmentStatus.UPLOADING.value
    attachment.uploaded_at = now()
    _flush(session)
    return attachment


def finalize_upload(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
) -> Attachment:
    """Den Upload zur Validierung annehmen - idempotent.

    Zwei gleichzeitige Aufrufe duerfen genau einen Validierungslauf
    erzeugen. Die Zeile wird deshalb gesperrt, bevor ihr Zustand gelesen
    wird; der zweite Aufruf sieht dann bereits VALIDATING und stellt keine
    zweite Aufgabe ein.
    """
    attachment = require_writable(session, Attachment, context, attachment_id)
    gesperrt = session.execute(
        select(Attachment).where(Attachment.id == attachment.id).with_for_update()
    ).scalar_one()

    if gesperrt.status == AttachmentStatus.VALIDATING.value:
        return gesperrt
    if gesperrt.status != AttachmentStatus.UPLOADING.value:
        raise ConflictError(
            "The upload has not been transferred.",
            ErrorCode.ATTACHMENT_NOT_READY,
        )

    gesperrt.status = AttachmentStatus.VALIDATING.value
    queue.enqueue(session, ATTACHMENT_VALIDATION, {"attachmentId": str(gesperrt.id)})
    _flush(session)
    return gesperrt


def get_attachment(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
) -> Attachment:
    attachment = require_readable(session, Attachment, context, attachment_id)
    if attachment.status in (
        AttachmentStatus.DELETING.value,
        AttachmentStatus.DELETE_FAILED.value,
    ):
        # Fachlich sofort unsichtbar (M2-D11). Dass die Zeile technisch noch
        # existiert, weil der Providercleanup laeuft, ist keine Auskunft.
        raise Attachment.privacy_absence.error()
    return attachment


def authorize_read(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
    target: ReadTarget,
) -> Attachment:
    """Pruefen, ob gelesen werden darf - und zwar jetzt.

    Die Parentangabe des Clients ist kein Capability-Token. Sie wird nicht
    geglaubt, sondern gegen den tatsaechlichen Zustand geprueft.
    """
    attachment = get_attachment(session, context, attachment_id)
    if attachment.status != AttachmentStatus.READY.value:
        raise _not_ready()

    if target.parent_type is not None:
        # Bindung kommt im Media-Integrationsslice. Bis dahin gibt es kein
        # gebundenes Attachment, also auch keinen Parent, der Zugriff
        # verleihen koennte - fail-closed statt vorgetaeuschter Pruefung.
        raise Attachment.privacy_absence.error()

    if attachment.owner_id != context.account_id:
        raise Attachment.privacy_absence.error()
    if _binding_window_expired(attachment):
        raise Attachment.privacy_absence.error()
    return attachment


def _binding_window_expired(attachment: Attachment) -> bool:
    if attachment.ready_at is None:
        return True
    bereit = attachment.ready_at
    if bereit.tzinfo is None:
        bereit = bereit.replace(tzinfo=UTC)
    return now() - bereit > BINDING_WINDOW


def open_content(attachment: Attachment, *, variant: str = ORIGINAL_VARIANT) -> BinaryIO:
    return get_media_store().open(storage_key_for(attachment, variant))


def delete_attachment(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    """Fachlich sofort unsichtbar, Providercleanup asynchron (M2-D11)."""
    attachment = require_writable(session, Attachment, context, attachment_id)
    if attachment.version != expected_version:
        raise ConflictError(
            "The resource was changed since it was loaded.",
            ErrorCode.RESOURCE_VERSION_CONFLICT,
        )
    mark_for_deletion(session, attachment)
    _flush(session)


def mark_for_deletion(session: Session, attachment: Attachment) -> None:
    attachment.status = AttachmentStatus.DELETING.value


def purge(session: Session, attachment: Attachment) -> bool:
    """Providerobjekte und Zeile entfernen. Gibt zurueck, ob es geklappt hat.

    Der Storagefehler darf die fachliche Unsichtbarkeit nicht zuruecknehmen:
    scheitert das Loeschen, bleibt die Zeile als DELETE_FAILED liegen und
    wird erneut versucht - sie wird nicht wieder sichtbar.
    """
    store = get_media_store()
    try:
        store.delete(storage_key_for(attachment, ORIGINAL_VARIANT))
        if attachment.has_thumbnail:
            store.delete(storage_key_for(attachment, THUMBNAIL_VARIANT))
    except OSError:
        attachment.status = AttachmentStatus.DELETE_FAILED.value
        log.warning("attachment purge failed", extra={"attachmentId": str(attachment.id)})
        return False
    session.delete(attachment)
    return True


def _fail(attachment: Attachment, code: str) -> None:
    attachment.status = AttachmentStatus.FAILED.value
    attachment.failure_code = code
    attachment.failed_at = now()


def validate(session: Session, attachment_id: UUID) -> None:
    """Der Validierungslauf. Laeuft im Worker, nie im Requestpfad.

    Reihenfolge nach Abschnitt 7 der Media-Pipeline: erst pruefen, dann
    nach M2-D14 bereinigt speichern, dann `READY`. Die Variante nach
    M2-D15 entsteht danach und ausserhalb dieser Kette - ihr Fehlschlag ist
    ein Darstellungs- und kein Sicherheitsproblem.
    """
    attachment = session.get(Attachment, attachment_id, with_for_update=True)
    if attachment is None or attachment.status != AttachmentStatus.VALIDATING.value:
        # Abgebrochen, geloescht oder schon verarbeitet. Kein Fehler.
        return

    rule = rule_for(attachment.declared_mime_type)
    if rule is None or not rule.supported:
        _fail(attachment, ErrorCode.ATTACHMENT_TYPE_NOT_ALLOWED)
        return

    store = get_media_store()
    schluessel = storage_key_for(attachment)
    if not store.exists(schluessel):
        _fail(attachment, ErrorCode.ATTACHMENT_VALIDATION_FAILED)
        return

    with store.open(schluessel) as quelle:
        roh = quelle.read()

    if len(roh) > rule.max_size:
        _fail(attachment, ErrorCode.ATTACHMENT_TOO_LARGE)
        return

    try:
        verarbeitet = images.process(roh, rule)
    except images.ImageRejectedError as error:
        _fail(attachment, error.code)
        return

    store.put(schluessel, io.BytesIO(verarbeitet.content), verarbeitet.mime_type)

    attachment.mime_type = verarbeitet.mime_type
    attachment.size = len(verarbeitet.content)
    attachment.width = verarbeitet.width
    attachment.height = verarbeitet.height
    attachment.payload = AttachmentPayload(
        original_name=attachment.payload.original_name,
        captured_at=verarbeitet.captured_at,
        orientation=verarbeitet.orientation,
    )

    if verarbeitet.thumbnail is not None:
        try:
            store.put(
                storage_key_for(attachment, THUMBNAIL_VARIANT),
                io.BytesIO(verarbeitet.thumbnail),
                "image/jpeg",
            )
        except OSError:
            log.warning("thumbnail store failed", extra={"attachmentId": str(attachment.id)})
        else:
            attachment.has_thumbnail = True

    attachment.status = AttachmentStatus.READY.value
    attachment.ready_at = now()
    attachment.failure_code = None


def expired(reference: datetime | None, retention: timedelta) -> bool:
    if reference is None:
        return False
    zeitpunkt = reference if reference.tzinfo is not None else reference.replace(tzinfo=UTC)
    return now() - zeitpunkt > retention
