"""Die Grenze zwischen Metadaten und schützenswertem Inhalt.

Im ersten Release gibt es KEINE Ende-zu-Ende-Verschlüsselung. Dieses Modul
implementiert sie nicht und darf nicht so vermarktet werden.

Was es tut: es zieht die Trennlinie jetzt, damit sie später nicht durch die
ganze Anwendung gezogen werden muss.

    Metadata                 ProtectedPayload
    ------------------       -----------------
    id, space_id             title
    author_id                body
    happened_on              weitere sensible Felder
    created_at
    crypto_version

In Version 1 ist der Payload Klartext, `crypto_version = 0`. Später
enthält dasselbe Feld Ciphertext, den der Client erzeugt hat, und der
Server sieht ihn nie im Klartext.

Die Konsequenz für alles, was darauf aufbaut: Dashboard, Rückblicke,
Regeln und Benachrichtigungen sollen mit Metadaten auskommen. Was den
Klartext braucht, funktioniert nach der Umstellung nicht mehr - und das
soll beim Schreiben auffallen, nicht Jahre später.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict

CRYPTO_VERSION_PLAINTEXT = 0
"""Klartext. Version 1 des Produkts."""

CRYPTO_VERSION_CLIENT_SEALED = 1
"""Reserviert: clientseitig verschlüsselt. Noch nicht implementiert."""


class ProtectedPayload(BaseModel):
    """Basis für den schützenswerten Teil eines Fachobjekts.

    Fachobjekte leiten davon ab und ergänzen ihre sensiblen Felder. Der Rest
    des Objekts - alles, was zum Sortieren, Filtern und Verknüpfen nötig ist -
    bleibt außerhalb.
    """

    model_config = ConfigDict(extra="forbid")

    crypto_version: ClassVar[int] = CRYPTO_VERSION_PLAINTEXT

    def seal(self) -> dict[str, Any]:
        """Den Payload in die Form bringen, die persistiert wird.

        Heute eine verlustfreie Abbildung nach JSON. Später der Ort, an dem
        aus dem Klartext ein Ciphertext wird - beziehungsweise an dem
        auffällt, dass der Server den Klartext gar nicht mehr besitzt.
        """
        return self.model_dump(mode="json")

    @classmethod
    def unseal(cls, stored: dict[str, Any] | None) -> Self:
        """Den gespeicherten Payload zurücklesen.

        Ein fehlender Payload ergibt ein leeres Objekt statt einer Ausnahme:
        nach der Umstellung auf echte Verschlüsselung wird es Zeilen geben,
        die der Server nicht lesen kann. Sie dürfen eine Liste nicht
        umwerfen.
        """
        return cls.model_validate(stored or {})


def is_readable_by_server(crypto_version: int) -> bool:
    """Kann der Server den Inhalt dieser Zeile lesen?

    Gedacht für abgeleitete Funktionen, die auf Klartext angewiesen sind.
    Sie sollen die Zeile überspringen können, statt zu raten.
    """
    return crypto_version == CRYPTO_VERSION_PLAINTEXT
