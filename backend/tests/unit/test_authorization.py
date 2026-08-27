"""Die Autorisierungsgrundlage ohne Datenbank.

Geprueft wird hier die Form: welche Klassen es gibt, welche der Server
durchsetzen kann, wie die Bedingung aussieht, die er daraus baut, und ob
das Mixin von mehreren Domaenen benutzbar ist. Ob die Bedingung im echten
PostgreSQL das Richtige tut, steht in den Integrationstests.
"""

from __future__ import annotations

import re
from typing import ClassVar
from uuid import UUID

import pytest
from sqlalchemy import MetaData, String, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sidebyside.authorization import (
    ENFORCEABLE_PRIVACY_CLASSES,
    Access,
    AuthorizationContext,
    PrivacyClass,
    PrivateResourceMixin,
    ResourceAbsence,
    SharedWrite,
    access_clause,
    privacy_clause,
    readable,
    writable,
)
from sidebyside.authorization.rules import rules_for
from sidebyside.core.ids import new_id
from sidebyside.db.base import NAMING_CONVENTION


class Probenbasis(DeclarativeBase):
    """Eine eigene Metadata, damit diese Testmodelle nichts registrieren.

    Sie werden nur uebersetzt, nie angelegt. Der Punkt dieser Datei ist,
    dass zwei verschiedene Domaenen dasselbe Mixin benutzen koennen - dafuer
    braucht es keine Tabellen, nur zwei Modelle.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Sonde(PrivateResourceMixin, Probenbasis):
    __tablename__ = "sonden"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    label: Mapped[str] = mapped_column(String(32))


class ZweiteSonde(PrivateResourceMixin, Probenbasis):
    __tablename__ = "zweite_sonden"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    note: Mapped[str] = mapped_column(String(32))


class GemeinsameSonde(PrivateResourceMixin, Probenbasis):
    """Eine Domaene, die nach M3-D01 gemeinsam geschrieben wird."""

    __tablename__ = "gemeinsame_sonden"

    shared_write: ClassVar[SharedWrite] = SharedWrite.COLLABORATIVE

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    label: Mapped[str] = mapped_column(String(32))


KONTEXT = AuthorizationContext(account_id=new_id(), space_id=new_id())


class TestPrivacyKlassen:
    def test_die_spezifikation_ist_vollstaendig_abgebildet(self) -> None:
        """Abschnitt 7 der Master-Spezifikation, wortgleich."""
        assert {klasse.value for klasse in PrivacyClass} == {
            "SPACE_SHARED",
            "OWNER_ONLY",
            "TEMPORARY_SHARED",
            "EPHEMERAL_CONTEXT",
            "SYSTEM_METADATA",
        }

    def test_es_gibt_keine_oeffentliche_klasse(self) -> None:
        assert not any("PUBLIC" in klasse.value for klasse in PrivacyClass)

    def test_durchsetzbar_ist_heute_nur_was_eine_regel_hat(self) -> None:
        assert set(ENFORCEABLE_PRIVACY_CLASSES) == {
            PrivacyClass.SPACE_SHARED,
            PrivacyClass.OWNER_ONLY,
        }

    @pytest.mark.parametrize("access", list(Access))
    def test_speicherbar_und_regelbar_decken_sich(self, access: Access) -> None:
        """Sonst gaebe es Zeilen, deren Schutz niemand einloest - oder eine
        Regel, die auf nichts trifft."""
        assert set(rules_for(access)) == set(ENFORCEABLE_PRIVACY_CLASSES)

    def test_die_spalte_laesst_nur_durchsetzbare_klassen_zu(self) -> None:
        erlaubt = set(Sonde.__table__.c.privacy_class.type.enums)
        assert erlaubt == {klasse.value for klasse in ENFORCEABLE_PRIVACY_CLASSES}
        assert "TEMPORARY_SHARED" not in erlaubt


class TestBedingung:
    def _sql(self, access: Access) -> str:
        return str(
            access_clause(Sonde, KONTEXT, access).compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )

    def test_der_space_steht_immer_davor(self) -> None:
        """Ohne die Mandantenbedingung saehe ein Eigentuemer seine Zeile
        auch in einem Space, in dem er nicht mehr ist."""
        for access in Access:
            assert f"sonden.space_id = '{KONTEXT.space_id}'" in self._sql(access)

    def test_owner_only_haengt_am_eigentuemer(self) -> None:
        sql = self._sql(Access.READ)
        assert "OWNER_ONLY" in sql
        assert f"sonden.owner_id = '{KONTEXT.account_id}'" in sql

    def test_space_shared_ist_beim_lesen_nicht_an_den_eigentuemer_gebunden(self) -> None:
        sql = self._sql(Access.READ)
        geteilt = sql.split("SPACE_SHARED")[1].split("OR")[0]
        assert "owner_id" not in geteilt

    def test_geschrieben_wird_nur_vom_eigentuemer(self) -> None:
        """Auch Geteiltes: der Autor bearbeitet, der Partner liest."""
        sql = self._sql(Access.WRITE)
        assert sql.count("owner_id") == 2

    def test_eine_klasse_ohne_regel_kommt_in_der_bedingung_nicht_vor(self) -> None:
        sql = self._sql(Access.READ)
        for klasse in set(PrivacyClass) - set(ENFORCEABLE_PRIVACY_CLASSES):
            assert klasse.value not in sql

    def test_ohne_jede_regel_bleibt_alles_unsichtbar(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Fail closed: ein Vergessen macht unsichtbar, nicht sichtbar.

        Waere die leere Bedingung wahr statt falsch, wuerde ein Fehler beim
        Eintragen einer Regel den gesamten Bestand freigeben.
        """
        from sidebyside.authorization import rules

        monkeypatch.setattr(rules, "_RULES", {Access.READ: {}})
        sql = str(privacy_clause(Sonde, KONTEXT, Access.READ).compile(dialect=postgresql.dialect()))
        assert sql.strip().lower() == "false"


class TestSchreibform:
    """`SPACE_SHARED` beantwortet die Lesefrage, nicht die Schreibfrage.

    Beide Formen leben unter derselben Privacy-Klasse: Memory und
    Milestone bleiben author-only (Spezifikation, Abschnitt 14), Wish,
    Plan, Place, Chapter und Collection sind collaborative write (M3-D01).
    Welche gilt, sagt das Modell - nicht der Endpunkt.
    """

    def _sql(self, modell: type, access: Access) -> str:
        return str(
            access_clause(modell, KONTEXT, access).compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )

    def test_der_standard_ist_die_engere_form(self) -> None:
        """Ein vergessener Eintrag macht nichts versehentlich schreibbar."""
        assert PrivateResourceMixin.shared_write is SharedWrite.AUTHOR_ONLY

    def test_gemeinsames_schreiben_haengt_nicht_am_ersteller(self) -> None:
        sql = self._sql(GemeinsameSonde, Access.WRITE)
        geteilt = sql.split("SPACE_SHARED")[1].split("OR")[0]
        assert "owner_id" not in geteilt

    def test_der_space_steht_auch_dort_davor(self) -> None:
        """Sonst duerfte ein Ex-Partner weiterschreiben."""
        sql = self._sql(GemeinsameSonde, Access.WRITE)
        assert f"gemeinsame_sonden.space_id = '{KONTEXT.space_id}'" in sql

    def test_owner_only_bleibt_auch_bei_gemeinsamem_schreiben_beim_eigentuemer(self) -> None:
        """Collaborative write ist eine Aussage ueber geteilte Zeilen.

        Traegt dieselbe Domaene spaeter auch `OWNER_ONLY`-Zeilen, darf die
        Ansage sie nicht mitreissen - dort ist der Partner kein Mitautor.
        """
        sql = self._sql(GemeinsameSonde, Access.WRITE)
        privat = sql.split("OWNER_ONLY")[1]
        assert f"gemeinsame_sonden.owner_id = '{KONTEXT.account_id}'" in privat

    def test_die_ansage_gilt_nur_der_eigenen_domaene(self) -> None:
        assert Sonde.shared_write is SharedWrite.AUTHOR_ONLY
        assert "owner_id" in self._sql(Sonde, Access.WRITE).split("SPACE_SHARED")[1].split("OR")[0]

    def test_lesen_bleibt_von_der_schreibform_unberuehrt(self) -> None:
        """Die Ansage betrifft das Schreiben - gelesen wurde schon vorher geteilt."""
        gemeinsam = self._sql(GemeinsameSonde, Access.READ)
        author_only = self._sql(Sonde, Access.READ)
        assert gemeinsam.replace("gemeinsame_sonden", "sonden") == author_only


class TestAbwesenheit:
    def test_eine_domaene_antwortet_immer_gleich(self) -> None:
        absence = ResourceAbsence("Probe not found.", "PROBE_NOT_FOUND")
        fehler = absence.error()
        assert fehler.status == 404
        assert fehler.code == "PROBE_NOT_FOUND"
        assert fehler.detail == "Probe not found."

    def test_ohne_eigene_angabe_bleibt_es_neutral(self) -> None:
        assert PrivateResourceMixin.privacy_absence.code == "RESOURCE_NOT_FOUND"


class TestWiederverwendbarkeit:
    """Zwei Domaenen, ein Mixin - kein kopierter Guard je Tabelle."""

    @pytest.mark.parametrize("modell", [Sonde, ZweiteSonde])
    def test_beide_bekommen_dieselben_spalten(self, modell: type) -> None:
        assert {"space_id", "owner_id", "privacy_class"} <= set(modell.__table__.c.keys())

    @pytest.mark.parametrize("modell", [Sonde, ZweiteSonde])
    def test_beide_bekommen_ihre_eigene_pruefbedingung(self, modell: type) -> None:
        namen = {
            constraint.name
            for constraint in modell.__table__.constraints
            if constraint.name is not None
        }
        assert f"ck_{modell.__tablename__}_privacy_class" in namen

    def test_die_bedingung_nennt_die_richtige_tabelle(self) -> None:
        sql = str(access_clause(ZweiteSonde, KONTEXT, Access.READ))
        assert "zweite_sonden.space_id" in sql
        # Wortgrenze: "zweite_sonden" enthaelt "sonden" als Teilzeichenkette.
        assert re.search(r"(?<![_a-z])sonden\.", sql) is None

    def test_jede_domaene_bleibt_bei_ihrer_eigenen_tabelle(self) -> None:
        """Keine gemeinsame Universal-Content-Tabelle."""
        assert Sonde.__table__ is not ZweiteSonde.__table__


class TestFertigeStatements:
    """`readable` und `writable` sind der Einstieg, den Domaenen benutzen.

    Sie tragen die Bedingung bereits, bevor eine Domaene Filter, Sortierung
    oder Grenzen anhaengt - deshalb muss sie hier stehen und nicht erst
    beim Aufrufer."""

    def test_lesen_traegt_die_lesebedingung(self) -> None:
        assert str(readable(Sonde, KONTEXT)) == str(
            select(Sonde).where(access_clause(Sonde, KONTEXT, Access.READ))
        )

    def test_schreiben_traegt_die_schreibbedingung(self) -> None:
        assert str(writable(Sonde, KONTEXT)) == str(
            select(Sonde).where(access_clause(Sonde, KONTEXT, Access.WRITE))
        )

    def test_die_beiden_bedingungen_sind_nicht_dieselbe(self) -> None:
        assert str(readable(Sonde, KONTEXT)) != str(writable(Sonde, KONTEXT))
