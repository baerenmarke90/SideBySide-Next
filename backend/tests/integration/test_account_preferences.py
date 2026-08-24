"""Die Schreibgrenze fuer Zeitzone und Locale, gegen die Datenbank."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from sidebyside.core.clock import today_in
from sidebyside.core.errors import ValidationError
from sidebyside.identity import preferences
from tests.conftest import make_account, requires_database

pytestmark = [pytest.mark.integration, requires_database]


class TestSchreibgrenze:
    def test_gueltige_werte_werden_gespeichert(self, session: Session) -> None:
        konto = make_account(session)
        preferences.set_preferences(session, konto, timezone="Pacific/Auckland", locale="en_nz")
        session.flush()

        session.expire(konto)
        assert konto.timezone == "Pacific/Auckland"
        assert konto.locale == "en-NZ"

    def test_ungueltige_zeitzone_wird_nicht_persistiert(self, session: Session) -> None:
        konto = make_account(session)
        vorher = konto.timezone

        with pytest.raises(ValidationError):
            preferences.set_preferences(session, konto, timezone="Europe/Berlinn")
        session.flush()

        session.expire(konto)
        assert konto.timezone == vorher

    def test_ein_ungueltiger_wert_laesst_den_anderen_unveraendert(self, session: Session) -> None:
        """Kein halb geaenderter Account: erst pruefen, dann zuweisen."""
        konto = make_account(session)
        vorher = (konto.timezone, konto.locale)

        with pytest.raises(ValidationError):
            preferences.set_preferences(
                session, konto, timezone="Pacific/Auckland", locale="deutsch"
            )
        session.flush()

        session.expire(konto)
        assert (konto.timezone, konto.locale) == vorher

    def test_nur_ein_feld_zu_setzen_laesst_das_andere_stehen(self, session: Session) -> None:
        konto = make_account(session)
        preferences.set_preferences(session, konto, locale="fr-FR")
        session.flush()

        session.expire(konto)
        assert konto.locale == "fr-FR"
        assert konto.timezone == "Europe/Berlin"

    def test_die_gespeicherte_zone_traegt_die_tagesgrenze(self, session: Session) -> None:
        """Der Sinn der Pruefung: der fachliche Tag haengt an diesem Wert."""
        konto = make_account(session)
        preferences.set_preferences(session, konto, timezone="Pacific/Auckland")
        session.flush()

        assert today_in(konto.timezone) == today_in("Pacific/Auckland")


class TestAltbestand:
    def test_lesen_bleibt_fail_safe(self, session: Session) -> None:
        """Ein bereits gespeicherter unbrauchbarer Wert darf keine Anzeige zerlegen."""
        konto = make_account(session)
        konto.timezone = "Kein/Ort"
        session.flush()

        assert today_in(konto.timezone) is not None
