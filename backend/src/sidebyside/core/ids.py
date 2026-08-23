"""Identifikatoren für persistente Domain-Objekte.

UUIDv7 statt fortlaufender Zahlen. Eine hochzählbare öffentliche ID verrät
Bestandsgrößen und lädt zum Durchprobieren ein; beides ist bei einem
Mandantensystem ein Sicherheitsproblem, kein Schönheitsfehler.

UUIDv7 trägt die Zeit in den führenden Bits und ist damit sortierbar. Als
Primärschlüssel bleibt der Index dadurch weitgehend anhängend, statt bei
jedem Insert an einer zufälligen Stelle aufzubrechen.
"""

from __future__ import annotations

from uuid import UUID

from uuid6 import uuid7


def new_id() -> UUID:
    """Ein neuer Identifikator für ein Domain-Objekt."""
    return uuid7()


def parse_id(value: str) -> UUID | None:
    """Eine ID aus einer Zeichenkette, oder None wenn sie keine ist.

    Bewusst ohne Ausnahme: eine fehlgeformte ID aus einer Anfrage ist ein
    erwarteter Fall und muss zu einer sauberen Antwort führen, nicht zu
    einem Fehler 500.
    """
    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None
