"""Aus einer Privacy-Klasse wird eine Bedingung fuer die Abfrage.

Der entscheidende Punkt ist, dass hier ein SQL-Ausdruck entsteht und kein
Wahrheitswert. Eine Regel, die erst auf einer geladenen Zeile antwortet,
kommt zu spaet: die Zeile war dann schon im Speicher, in der Antwortgroesse
und moeglicherweise im Log. Der Filter gehoert in die Abfrage.

Erweitert wird die Tabelle der Regeln, nicht der Aufrufort. Eine neue
Klasse bekommt eine Funktion und einen Eintrag; alle bestehenden Domaenen
verhalten sich danach ohne Aenderung richtig.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from enum import StrEnum
from types import MappingProxyType

from sqlalchemy import ColumnElement, and_, false, or_, true

from sidebyside.authorization.models import PrivateResource
from sidebyside.authorization.privacy import AuthorizationContext, PrivacyClass, SharedWrite


class Access(StrEnum):
    """Die Absicht hinter einer Anfrage."""

    READ = "READ"
    WRITE = "WRITE"


AccessRule = Callable[[type[PrivateResource], AuthorizationContext], ColumnElement[bool]]
"""Eine Regel liefert die Bedingung, unter der eine Zeile ihrer Klasse zaehlt."""


def _the_whole_space(
    model: type[PrivateResource], context: AuthorizationContext
) -> ColumnElement[bool]:
    """Beide Partner. Die Mandantenbedingung steht bereits davor."""
    return true()


def _only_the_owner(
    model: type[PrivateResource], context: AuthorizationContext
) -> ColumnElement[bool]:
    """Nur der Eigentuemer - der Partner steht hier Fremden gleich."""
    return model.owner_id == context.account_id


_READ_RULES: Mapping[PrivacyClass, AccessRule] = MappingProxyType(
    {
        PrivacyClass.SPACE_SHARED: _the_whole_space,
        PrivacyClass.OWNER_ONLY: _only_the_owner,
    }
)


def _shared_write(
    model: type[PrivateResource], context: AuthorizationContext
) -> ColumnElement[bool]:
    """Die Schreibform, die die Domaene angesagt hat.

    Der Standard bleibt author-only: "Der Autor darf persoenlichen Text
    bearbeiten/loeschen. Partner darf gemeinsame Erinnerung lesen."
    (Spezifikation, Abschnitt 14). Die gemeinsamen M3-Planungs- und
    Listenressourcen sind nach M3-D01 ausdruecklich collaborative write -
    ein Wunsch gehoert dem Paar und nicht dem, der ihn zuerst getippt hat.

    Die Fallunterscheidung steht hier und nicht im Endpunkt. Sonst waere
    gemeinsames Schreiben eine Ausnahme je Route, und eine vergessene
    Ausnahme faellt niemandem auf.
    """
    if model.shared_write is SharedWrite.COLLABORATIVE:
        return _the_whole_space(model, context)
    return _only_the_owner(model, context)


_WRITE_RULES: Mapping[PrivacyClass, AccessRule] = MappingProxyType(
    {
        PrivacyClass.SPACE_SHARED: _shared_write,
        # Fuer OWNER_ONLY gibt es die Wahl nicht: dort ist der Partner
        # kein Mitautor, sondern ein Fremder.
        PrivacyClass.OWNER_ONLY: _only_the_owner,
    }
)

_RULES: Mapping[Access, Mapping[PrivacyClass, AccessRule]] = MappingProxyType(
    {
        Access.READ: _READ_RULES,
        Access.WRITE: _WRITE_RULES,
    }
)


def rules_for(access: Access) -> Mapping[PrivacyClass, AccessRule]:
    return _RULES[access]


def privacy_clause(
    model: type[PrivateResource],
    context: AuthorizationContext,
    access: Access,
) -> ColumnElement[bool]:
    """Die Bedingung fuer genau diese Absicht - ohne die Mandantenbedingung.

    Klassen ohne Eintrag erzeugen keinen Zweig. Damit faellt eine
    unbekannte oder noch nicht durchsetzbare Klasse auf `false` und nicht
    auf "durchgelassen": ein Vergessen macht Inhalte unsichtbar, nicht
    sichtbar.
    """
    branches = [
        and_(model.privacy_class == privacy_class.value, rule(model, context))
        for privacy_class, rule in rules_for(access).items()
    ]
    return or_(false(), *branches)


def access_clause(
    model: type[PrivateResource],
    context: AuthorizationContext,
    access: Access,
) -> ColumnElement[bool]:
    """Mandant und Privatsphaere in einer Bedingung.

    Die Reihenfolge ist keine Stilfrage: der Space steht immer davor. Waere
    nur die Eigentuemerbedingung im Ausdruck, wuerde ein Eigentuemer seine
    Zeile auch aus einem Space sehen, in dem er laengst nicht mehr ist.
    """
    return and_(model.space_id == context.space_id, privacy_clause(model, context, access))
