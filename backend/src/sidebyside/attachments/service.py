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
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from sidebyside.core.ids import parse_id
from sidebyside.jobs import queue
from sidebyside.media import build_storage_key, get_media_store, supports_signed_upload

log = logging.getLogger(__name__)

ATTACHMENT_VALIDATION = "attachment_validation"

BINDING_WINDOW = timedelta(minutes=60)
"""M2-D20: so lange darf ein READY Attachment ungebunden bleiben."""

ORIGINAL_VARIANT = "original"
THUMBNAIL_VARIANT = "thumbnail"

MAX_ORIGINAL_NAME = 255


@dataclass(frozen=True)
class ReadTarget:
    """Was der Aufrufer ueber die Bindung behauptet - oder eben nichts.

    Drei Faelle, die auseinandergehalten werden muessen. `NONE` aus dem
    API-Vertrag ist eine *Behauptung* des Clients, das Attachment sei
    ungebunden; sie ist nach M2-D24 bei einem gebundenen Attachment
    unzulaessig. Die interne Streamingroute dagegen behauptet gar nichts
    und laesst den Server die Bindung aufloesen.

    Beides in einem `parent_type is None` zusammenzufassen war ein Fehler:
    dann haette entweder die Behauptung nicht mehr gegolten oder die
    Streamingroute kein gebundenes Attachment mehr ausliefern koennen.
    """

    parent_type: str | None = None
    parent_id: UUID | None = None
    asserts_unbound: bool = False

    @classmethod
    def resolved_by_server(cls) -> ReadTarget:
        """Keine Behauptung - der Server sieht nach, woran es haengt."""
        return cls()

    @classmethod
    def unbound(cls) -> ReadTarget:
        """Der Aufrufer behauptet, es sei ungebunden."""
        return cls(asserts_unbound=True)

    @classmethod
    def parent(cls, parent_type: str, parent_id: UUID) -> ReadTarget:
        return cls(parent_type=parent_type, parent_id=parent_id)


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

    Beim presigned Transport sieht die API keinen Byte-Transfer. Dort wird
    PENDING deshalb erst unter demselben Row Lock zu UPLOADING, nachdem der
    Adapter das exakt gebundene Providerobjekt bestaetigt hat. Das ist nur
    die Beobachtung des Transfers - die Validierungsentscheidung bleibt
    unveraendert beim Worker.
    """
    attachment = require_writable(session, Attachment, context, attachment_id)
    gesperrt = session.execute(
        select(Attachment).where(Attachment.id == attachment.id).with_for_update()
    ).scalar_one()

    if gesperrt.status == AttachmentStatus.VALIDATING.value:
        return gesperrt

    store = get_media_store()
    if gesperrt.status == AttachmentStatus.PENDING.value and supports_signed_upload(store):
        if not store.exists(storage_key_for(gesperrt)):
            raise ConflictError(
                "The upload has not been transferred.",
                ErrorCode.ATTACHMENT_NOT_READY,
            )
        gesperrt.status = AttachmentStatus.UPLOADING.value
        gesperrt.uploaded_at = now()

    if gesperrt.status != AttachmentStatus.UPLOADING.value:
        raise ConflictError(
            "The upload has not been transferred.",
            ErrorCode.ATTACHMENT_NOT_READY,
        )

    gesperrt.status = AttachmentStatus.VALIDATING.value
    queue.enqueue(session, ATTACHMENT_VALIDATION, {"attachmentId": str(gesperrt.id)})
    _flush(session)
    return gesperrt


def _load_in_space(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
) -> Attachment:
    """Die Zeile im eigenen Space finden - ohne ueber ihre Klasse zu urteilen.

    Ein Attachment ist die einzige M2-Ressource, deren Lesbarkeit nicht aus
    der eigenen Privacy-Klasse folgt: gebunden entscheidet der Parent
    (Media-Pipeline, Abschnitt 8). Wuerde hier der Owner-only-Guard greifen,
    saehe der Partner das Bild einer gemeinsamen Memory nicht.

    Das ist keine zweite Sichtbarkeitsregel: die Entscheidung wird nur
    verschoben, nicht selbst getroffen - `authorize_read` fragt anschliessend
    fuer den Parent wieder die zentrale Autorisierung.
    """
    kennung = attachment_id if isinstance(attachment_id, UUID) else parse_id(attachment_id)
    if kennung is None:
        raise Attachment.privacy_absence.error()
    gefunden = session.execute(
        select(Attachment).where(
            Attachment.id == kennung,
            Attachment.space_id == context.space_id,
        )
    ).scalar_one_or_none()
    if gefunden is None:
        raise Attachment.privacy_absence.error()
    if gefunden.status in (
        AttachmentStatus.DELETING.value,
        AttachmentStatus.DELETE_FAILED.value,
    ):
        # Fachlich sofort unsichtbar (M2-D11). Dass die Zeile technisch noch
        # existiert, weil der Providercleanup laeuft, ist keine Auskunft.
        raise Attachment.privacy_absence.error()
    return gefunden


def get_attachment(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
) -> Attachment:
    """Die Metadaten - unter derselben zweistufigen Regel wie der Inhalt.

    Ein gebundenes Attachment ist fuer jeden lesbar, der seinen Parent
    lesen darf; ein ungebundenes nur fuer seinen Owner im Bindungsfenster.
    Beides muss hier gelten, sonst waere die Metadatenroute der Weg an der
    Regel vorbei.
    """
    from sidebyside.attachments import binding

    attachment = _load_in_space(session, context, attachment_id)
    tatsaechlich = binding.parent_of(session, attachment.id)
    if tatsaechlich is None:
        if attachment.owner_id != context.account_id:
            raise Attachment.privacy_absence.error()
        return attachment
    _require_readable_parent(session, context, *tatsaechlich)
    return attachment


def authorize_read(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | str,
    target: ReadTarget,
) -> Attachment:
    """Pruefen, ob gelesen werden darf - und zwar jetzt.

    Nach der Bindung folgt die Lesbarkeit ausschliesslich dem Parent. Der
    Attachment-Owner ist dann *kein* alternativer Lesepfad mehr: wer eine
    Memory nicht mehr lesen darf oder einen HeartMoment privat gestellt
    bekommen hat, kommt auch nicht ueber die Attachment-Route an ihr Bild.

    Die Parentangabe des Clients ist kein Capability-Token. Sie wird nicht
    geglaubt, sondern gegen die tatsaechliche Bindung geprueft.
    """
    from sidebyside.attachments import binding

    attachment = _load_in_space(session, context, attachment_id)
    if attachment.status != AttachmentStatus.READY.value:
        raise _not_ready()

    tatsaechlich = binding.parent_of(session, attachment.id)

    if tatsaechlich is None:
        # Ungebunden: nur der Owner, nur im Bindungsfenster (M2-D20/D24).
        if target.parent_type is not None:
            raise Attachment.privacy_absence.error()
        if attachment.owner_id != context.account_id:
            raise Attachment.privacy_absence.error()
        if binding_window_expired(attachment):
            raise Attachment.privacy_absence.error()
        return attachment

    if target.asserts_unbound:
        # M2-D24 gilt nur fuer ungebundene Uploads. Eine falsche Behauptung
        # wird abgewiesen und nicht stillschweigend korrigiert.
        raise Attachment.privacy_absence.error()

    parent_type, parent_id = tatsaechlich
    if target.parent_type is not None and (
        target.parent_type != parent_type or target.parent_id != parent_id
    ):
        # Eine falsche Parentangabe wird nicht korrigiert, sondern
        # abgewiesen - sonst waere sie ein Rateversuch mit Rueckmeldung.
        raise Attachment.privacy_absence.error()

    _require_readable_parent(session, context, parent_type, parent_id)
    return attachment


def _require_readable_parent(
    session: Session,
    context: AuthorizationContext,
    parent_type: str,
    parent_id: UUID,
) -> None:
    """Der Parent entscheidet - ueber dieselbe zentrale Autorisierung.

    Kein eigener Sichtbarkeitsausdruck: waere hier eine zweite Regel
    formuliert, koennte sie von der der Domaene abweichen, und die
    Attachment-Route waere der Weg daran vorbei.
    """
    from sidebyside.heart_moments.models import HeartMoment
    from sidebyside.memories.models import Memory

    modell = Memory if parent_type == "MEMORY" else HeartMoment
    try:
        require_readable(session, modell, context, parent_id)
    except NotFoundError as error:
        raise Attachment.privacy_absence.error() from error


def binding_window_expired(attachment: Attachment) -> bool:
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
