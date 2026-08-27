#!/usr/bin/env python3
"""Temporarily migrate the remaining #214 test engineering language to English.

This codemod is intentionally scoped to the integration-test files still
reported by the engineering-language audit. It rewrites Python identifiers
through tokenization and translates only engineering prose surfaces (comments,
docstrings, assertion messages, raised diagnostics). Ordinary string literals
are left untouched so product/locale fixtures and protocol data are preserved.

The file is temporary migration tooling for PR #219 and is removed once the
branch passes the authoritative audit and formatter.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

TARGETS = (
    Path("backend/tests/integration/test_attachments.py"),
    Path("backend/tests/integration/test_auth_flows.py"),
    Path("backend/tests/integration/test_cloud_auth_flows.py"),
    Path("backend/tests/integration/test_endpoint_matrix.py"),
    Path("backend/tests/integration/test_oidc.py"),
    Path("backend/tests/integration/test_places.py"),
    Path("backend/tests/integration/test_private_authorization.py"),
    Path("backend/tests/integration/test_sessions.py"),
    Path("backend/tests/integration/test_wishes.py"),
)

# Exact non-snake-case identifiers and domain-specific names.
EXACT_IDENTIFIERS = {
    "HERSTELLER": "MANUFACTURER",
    "KOMMENTAR": "COMMENT",
    "VERBINDUNG": "CONNECTION",
    "OEFFENTLICH": "PUBLIC_ENDPOINTS",
    "NUR_ANGEMELDET": "AUTHENTICATED_ONLY",
    "Endpunkt": "Endpoint",
    "Anbieter": "MockProvider",
    "TestLebenszyklus": "TestLifecycle",
    "TestOwnerGrenze": "TestOwnerBoundary",
    "TestLoeschenUndAufraeumen": "TestDeletionAndCleanup",
    "TestVerknuepfen": "TestLinking",
    "TestAbgelehnteToken": "TestRejectedTokens",
    "TestAnbieterAntwortetFalsch": "TestProviderFailures",
}

# Segment-level translations intentionally cover both variable names and test
# names. Transliteration variants are included because the legacy test suite
# used ASCII spellings such as "ueber" and "schluessel".
SEGMENTS = {
    "abgeschalteter": "disabled",
    "abgelehnten": "rejected",
    "abgelehnte": "rejected",
    "abgelehnt": "rejected",
    "abgelaufener": "expired",
    "abgelaufenes": "expired",
    "abgelaufene": "expired",
    "abgelaufen": "expired",
    "abgeschnittene": "truncated",
    "abgedeckt": "covered",
    "abmelden": "logout",
    "abmeldung": "logout",
    "abgewiesen": "rejected",
    "abweichung": "deviation",
    "adresse": "address",
    "adressen": "addresses",
    "aelteste": "oldest",
    "aendern": "change",
    "aendert": "changes",
    "aenderbar": "editable",
    "aenderung": "change",
    "aendert_nichts": "changes_nothing",
    "allererste": "very_first",
    "alte": "old",
    "alten": "old",
    "alter": "old",
    "anderem": "other",
    "anderen": "other",
    "anderer": "other",
    "andere": "other",
    "anders": "different",
    "angekuendigte": "declared",
    "angemeldet": "signed_in",
    "angemeldetes": "signed_in",
    "anmelden": "sign_in",
    "anmeldung": "sign_in",
    "anmeldeversuch": "sign_in_attempt",
    "anmeldeversuche": "sign_in_attempts",
    "anonym": "anonymous",
    "anonymer": "anonymous",
    "anbieter": "provider",
    "antwort": "response",
    "antworten": "responses",
    "aufraeumen": "cleanup",
    "aufgeraeumt": "cleaned_up",
    "auftraege": "jobs",
    "aufgerufen": "called",
    "ausserhalb": "outside",
    "ausdrueckliches": "explicit",
    "ausdruecklich": "explicitly",
    "auskunft": "disclosure",
    "ausgestellt": "issued",
    "authentifiziert": "authenticated",
    "bedingung": "condition",
    "beendet": "ended",
    "beendete": "ended",
    "beginnt": "starts",
    "begonnen": "started",
    "bekannt": "known",
    "bekannte": "known",
    "bekannten": "known",
    "bekommt": "gets",
    "benoetigt": "requires",
    "bereich": "range",
    "beschreibung": "descriptor",
    "bestaetigt": "verifies",
    "bestaetigen": "verify",
    "bestaetigung": "verification",
    "betroffen": "affected",
    "bewegt": "moves",
    "bild": "image",
    "bilder": "images",
    "bindungsfenster": "binding_window",
    "bleibt": "remains",
    "braucht": "requires",
    "bremse": "rate_limit",
    "cursor": "cursor",
    "darf": "may",
    "daten": "data",
    "datei": "file",
    "dauerhaft": "permanently",
    "derselben": "same",
    "desselben": "same",
    "dieselbe": "same",
    "dieselben": "same",
    "diesen": "this",
    "direkt": "directly",
    "domaene": "domain",
    "dritten": "third",
    "echt": "real",
    "echte": "real",
    "echten": "real",
    "eigenen": "own",
    "eigene": "own",
    "eigenes": "own",
    "eigentuemlichkeit": "property",
    "eindeutig": "unique",
    "eine": "a",
    "einen": "a",
    "einem": "a",
    "einer": "a",
    "ein": "a",
    "eingeloeste": "redeemed",
    "einladung": "invitation",
    "eintrag": "entry",
    "endpunkt": "endpoint",
    "endpunkte": "endpoints",
    "entfernen": "removing",
    "enthaelt": "contains",
    "entsteht": "is_created",
    "entwertet": "invalidates",
    "erfolg": "success",
    "erfolgreich": "successful",
    "erfolgreiche": "successful",
    "erfolgreicher": "successful",
    "erfundenen": "invented",
    "erfundener": "invented",
    "erfundene": "invented",
    "erneuern": "refresh",
    "erneuert": "refreshed",
    "erneute": "repeated",
    "erneut": "again",
    "erreicht": "reaches",
    "erst": "initial",
    "erste": "first",
    "ersten": "first",
    "ersteller": "creator",
    "erzeugt": "creates",
    "erzeugen": "create",
    "es": "it",
    "faehigkeiten": "capabilities",
    "faehigkeit": "capability",
    "faengt": "catches",
    "falsch": "wrong",
    "falsche": "wrong",
    "falscher": "wrong",
    "fehlend": "missing",
    "fehlende": "missing",
    "fehlender": "missing",
    "fehlgeformte": "malformed",
    "fehlgeformter": "malformed",
    "fehlversuche": "failed_attempts",
    "fehler": "error",
    "fehlerantwort": "error_response",
    "fertiges": "ready",
    "finalisieren": "finalize",
    "finalisiert": "finalized",
    "frisch": "fresh",
    "frische": "fresh",
    "frischer": "fresh",
    "fremd": "foreign",
    "fremde": "foreign",
    "fremden": "foreign",
    "fremder": "foreign",
    "fremdes": "foreign",
    "fremdschreibversuch": "foreign_write_attempt",
    "fremdschluessel": "foreign_key",
    "funktioniert": "works",
    "fuer": "for",
    "ganz": "full",
    "gegenstelle": "mock_provider",
    "gegenseite": "other_side",
    "geguckt": "checked",
    "geheimnis": "secret",
    "geaendert": "updated",
    "gehasht": "hashed",
    "geloeschte": "deleted",
    "geloescht": "deleted",
    "geloest": "cleared",
    "genau": "exactly",
    "generation": "generation",
    "generationen": "generations",
    "geratener": "guessed",
    "geraet": "device",
    "geraetesitzung": "device_session",
    "gescheitertes": "failed",
    "gescheitert": "failed",
    "gespeichert": "stored",
    "gestrippt": "stripped",
    "getarnter": "disguised",
    "geteilt": "shared",
    "geteiltes": "shared",
    "geteilte": "shared",
    "gleitendes": "sliding",
    "grenze": "boundary",
    "grenzwerte": "boundary_values",
    "groesse": "size",
    "gueltig": "valid",
    "gueltige": "valid",
    "gueltigen": "valid",
    "gueltiges": "valid",
    "haelt": "keeps",
    "haengt": "belongs",
    "handelnden": "actor",
    "heisst": "means",
    "hilft": "helps",
    "hinein": "in",
    "historie": "history",
    "inhalt": "content",
    "ist": "is",
    "ja": "yes",
    "jede": "every",
    "jeden": "every",
    "jeder": "every",
    "jetzt": "now",
    "kaputter": "malformed",
    "kann": "can",
    "keine": "no",
    "keinen": "no",
    "kein": "no",
    "kennung": "attachment_id",
    "klartext": "plaintext",
    "klartextfeld": "plaintext_field",
    "klein": "lowercase",
    "kommt": "gets",
    "konto": "account",
    "konten": "accounts",
    "kontobezogene": "account_scoped",
    "koerper": "body",
    "koordinaten": "coordinates",
    "koordinate": "coordinate",
    "kopf": "headers",
    "kopfzeilen": "headers",
    "krumme": "malformed",
    "krumm": "malformed",
    "kurzes": "short",
    "kurze": "short",
    "kurz": "short",
    "laesst": "allows",
    "lade": "upload",
    "laufende": "active",
    "lebt": "lives",
    "leerer": "empty",
    "lesbar": "readable",
    "liest": "reads",
    "liefert": "returns",
    "link": "link",
    "liste": "list",
    "loeschen": "delete",
    "loescht": "deletes",
    "mailweg": "mail_transport",
    "meldet": "reports",
    "meldungen": "messages",
    "metadaten": "metadata",
    "mit": "with",
    "mittlere": "middle",
    "moeglich": "possible",
    "muss": "must",
    "nach": "after",
    "nachher": "afterwards",
    "nachtraeglich": "later",
    "nachweis": "proof",
    "naechsten": "next",
    "neue": "new",
    "neuen": "new",
    "neuer": "new",
    "neues": "new",
    "neu": "new",
    "nicht": "not",
    "nichts": "nothing",
    "null": "null",
    "nur": "only",
    "oeffentliche": "public",
    "oeffentlich": "public",
    "ohne": "without",
    "ort": "place",
    "orte": "places",
    "owner": "owner",
    "paar": "couple",
    "parameter": "parameters",
    "parentreferenz": "parent_reference",
    "passwort": "password",
    "passwortanmeldung": "password_sign_in",
    "passwortwechsel": "password_change",
    "pfad": "path",
    "plaene": "plans",
    "plan": "plan",
    "postfach": "mailbox",
    "privat": "private",
    "private": "private",
    "privaten": "private",
    "pruefung": "check",
    "prueft": "checks",
    "pruefung": "check",
    "pruefungen": "checks",
    "pruefung": "check",
    "puffer": "buffer",
    "raeumt": "cleans_up",
    "rechtmaessigen": "legitimate",
    "regelmaessiges": "regular",
    "relation": "relation",
    "relationen": "relations",
    "reihenfolge": "order",
    "ressource": "resource",
    "ressourcen": "resources",
    "ressourcen_id": "resource_id",
    "ressourcen_platzhalter": "resource_placeholders",
    "roh": "raw",
    "rumpf": "body",
    "schleife": "loop",
    "schluessel": "key",
    "schwaches": "weak",
    "sendet": "sends",
    "sende": "send",
    "sieht": "sees",
    "sind": "are",
    "sitzung": "session_data",
    "sitzungen": "sessions",
    "solange": "while",
    "sonden": "probes",
    "sondenabfragen": "probe_queries",
    "sondenrouter": "probe_router",
    "space": "space",
    "steht": "is_stored",
    "statusfilter": "status_filter",
    "stimmt": "matches",
    "tabelle": "table",
    "taugt": "works",
    "titel": "title",
    "titelkorrektur": "title_correction",
    "token": "token",
    "traegt": "carries",
    "treffer": "match",
    "trefferzahl": "result_count",
    "typ": "type",
    "ueber": "via",
    "ueberholen": "exceed",
    "ueberlebt": "survives",
    "uebertragen": "upload_response",
    "ueberschreitung": "oversize",
    "unbekannt": "unknown",
    "unbekannte": "unknown",
    "unbekannten": "unknown",
    "unbekannter": "unknown",
    "unbeteiligt": "unaffected",
    "unfug": "malformed",
    "ungueltig": "invalid",
    "unveraendert": "unchanged",
    "unveraendert": "unchanged",
    "veraltet": "stale",
    "veraltete": "stale",
    "veralteter": "stale",
    "verbrauchte": "consumed",
    "verbindung": "connection",
    "verboten": "forbidden",
    "verbraucht": "consumed",
    "verifier": "verifier",
    "verknuepfen": "link",
    "verknuepfung": "linking",
    "verliert": "loses",
    "verraet": "reveals",
    "verschiebt": "moves",
    "verschlossen": "closed",
    "versand": "delivery",
    "versuch": "attempt",
    "versuche": "attempts",
    "vertrag": "contract",
    "vollstaendig": "complete",
    "vom": "from",
    "vor": "before",
    "vorhandene": "existing",
    "vorhandenen": "existing",
    "waere": "would_be",
    "wartungsjob": "maintenance_job",
    "wechsel": "change",
    "welt": "scenario",
    "wenn": "when",
    "werte": "values",
    "widerrufen": "revoked",
    "widerrufene": "revoked",
    "widerrufener": "revoked",
    "widerruft": "revokes",
    "wiederverwendeter": "reused",
    "wiederherstellung": "recovery",
    "wird": "is",
    "wunsch": "wish",
    "zaehler": "counter",
    "zaehlt": "counts",
    "zaehlung": "count",
    "zeile": "row",
    "ziel": "target",
    "zielaufloesung": "target_resolution",
    "zuerst": "first",
    "zugang": "access_token",
    "zugriff": "access",
    "zurueck": "back",
    "zuruecksetzen": "reset",
    "zusatz": "request_kwargs",
    "zusaetzlicher": "additional",
    "zustand": "state",
    "zustaende": "states",
    "zweite": "second",
    "zweiten": "second",
    "zweimal": "second_time",
}

# Whole-word prose translations. These are deliberately broader than the
# identifier vocabulary because comments/docstrings carry grammar and rationale.
WORDS = {
    "Abbruch": "failure",
    "Account": "account",
    "Accounts": "accounts",
    "Adresse": "address",
    "Adressen": "addresses",
    "Anbieter": "provider",
    "Anfrage": "request",
    "Anfragen": "requests",
    "Anmelden": "Sign in",
    "Anmeldung": "sign-in",
    "Anmeldewege": "sign-in methods",
    "Anmeldeweg": "sign-in method",
    "Anmeldenachweise": "sign-in credentials",
    "Anmeldenachweis": "sign-in credential",
    "Anmeldeversuch": "sign-in attempt",
    "Aufnahmezeitpunkt": "capture timestamp",
    "Aufrufer": "caller",
    "Auskunft": "disclosure",
    "Bedingung": "condition",
    "Bremse": "rate limit",
    "Client": "client",
    "Datenbank": "database",
    "Endpunkt": "endpoint",
    "Endpunkte": "endpoints",
    "Ersteller": "creator",
    "Fehler": "error",
    "Fremdschluessel": "foreign key",
    "Gegenprobe": "countercheck",
    "Geraet": "device",
    "Grenze": "boundary",
    "Historie": "history",
    "Identitaet": "identity",
    "Klartextfeld": "plaintext field",
    "Konto": "account",
    "Konten": "accounts",
    "Koordinaten": "coordinates",
    "Mailweg": "mail transport",
    "Membership": "membership",
    "Nachweis": "proof",
    "Nachricht": "message",
    "Parent": "parent",
    "Passwort": "password",
    "Passwoerter": "passwords",
    "Plan": "plan",
    "Pruefung": "check",
    "Pruefungen": "checks",
    "Ressource": "resource",
    "Ressourcen": "resources",
    "Route": "route",
    "Schraegstrich": "slash",
    "Schluessel": "key",
    "Sitzung": "session",
    "Sitzungen": "sessions",
    "Space": "space",
    "Storage": "storage",
    "Tabelle": "table",
    "Token": "token",
    "Tokens": "tokens",
    "Verbindung": "connection",
    "Verhalten": "behavior",
    "Vertrag": "contract",
    "Wish": "wish",
    "Wunsch": "wish",
    "Zaehler": "counter",
    "Zeile": "row",
    "Ziel": "target",
    "Zugriff": "access",
    "abgeschaltet": "disabled",
    "abgelaufen": "expired",
    "abgelehnten": "rejected",
    "abgelehnt": "rejected",
    "abgewiesen": "rejected",
    "abhaengt": "depends",
    "abhaengig": "dependent",
    "abschiesst": "revokes",
    "aendert": "changes",
    "aenderbar": "editable",
    "aller": "all",
    "alte": "old",
    "alten": "old",
    "andere": "other",
    "anderen": "other",
    "anderer": "other",
    "anderswo": "elsewhere",
    "angekuendigte": "declared",
    "angemeldet": "signed in",
    "anlegen": "create",
    "anlegt": "creates",
    "anmelden": "sign in",
    "anonym": "anonymous",
    "auch": "also",
    "auf": "on",
    "aufgeraeumt": "cleaned up",
    "aufloesung": "resolution",
    "aus": "from",
    "ausfaellt": "fails",
    "ausfiltern": "filter out",
    "ausschliesslich": "exclusively",
    "aussen": "outside",
    "beendet": "ends",
    "beginnen": "start",
    "beginnt": "starts",
    "beim": "during",
    "bekommt": "gets",
    "benutzt": "used",
    "bereits": "already",
    "bestaetigen": "confirm",
    "bestaetigt": "confirms",
    "bleiben": "remain",
    "bleibt": "remains",
    "braucht": "requires",
    "dabei": "while doing so",
    "dann": "then",
    "darf": "may",
    "dass": "that",
    "dauerhaft": "permanently",
    "den": "the",
    "dem": "the",
    "der": "the",
    "des": "the",
    "die": "the",
    "dieselben": "the same",
    "dieser": "this",
    "dieses": "this",
    "direkt": "directly",
    "durch": "through",
    "ein": "a",
    "eine": "a",
    "einem": "a",
    "einen": "a",
    "einer": "a",
    "einmal": "once",
    "einen": "a",
    "eindeutige": "unique",
    "entgegennimmt": "accepts",
    "entscheidet": "decides",
    "entsteht": "is created",
    "entwertet": "invalidates",
    "er": "it",
    "erfolgreiche": "successful",
    "erfolgreichen": "successful",
    "erfunden": "invented",
    "erfundene": "invented",
    "erwarteter": "expected",
    "erzeugt": "creates",
    "es": "it",
    "faellt": "fails",
    "faengt": "catches",
    "falsch": "wrong",
    "fehlt": "is missing",
    "fehlen": "are missing",
    "fehlende": "missing",
    "fehlgeformt": "malformed",
    "fremden": "foreign",
    "fremder": "foreign",
    "fuer": "for",
    "ganz": "entirely",
    "geandert": "changed",
    "geaendert": "changed",
    "gebunden": "bound",
    "geglueckte": "successful",
    "gehoert": "belongs",
    "geht": "works",
    "gelöscht": "deleted",
    "geloescht": "deleted",
    "genau": "exactly",
    "gespeichert": "stored",
    "gestohlenes": "stolen",
    "gibt": "exists",
    "gleich": "same",
    "gleiche": "same",
    "greifen": "apply",
    "gueltig": "valid",
    "gueltige": "valid",
    "gueltigen": "valid",
    "hat": "has",
    "heisst": "means",
    "hier": "here",
    "hinein": "in",
    "im": "in the",
    "immer": "always",
    "ins": "into the",
    "ist": "is",
    "jede": "every",
    "jeden": "every",
    "jeder": "every",
    "kein": "no",
    "keine": "no",
    "keinen": "no",
    "klingt": "looks",
    "koennte": "could",
    "koennen": "can",
    "laeuft": "runs",
    "laesst": "allows",
    "lebt": "is alive",
    "liefe": "would run",
    "liest": "reads",
    "liegt": "is",
    "macht": "makes",
    "mehr": "more",
    "mehreren": "multiple",
    "meldet": "reports",
    "mit": "with",
    "moeglich": "possible",
    "muss": "must",
    "muessen": "must",
    "nach": "after",
    "nachdem": "after",
    "naechsten": "next",
    "nicht": "not",
    "nichts": "nothing",
    "noch": "still",
    "nur": "only",
    "oder": "or",
    "offen": "open",
    "oeffnet": "opens",
    "ohne": "without",
    "prueft": "checks",
    "pruefte": "would check",
    "rechtmaessigen": "legitimate",
    "regelmaessiges": "regular",
    "rotierter": "rotated",
    "salzt": "salts",
    "schreibt": "writes",
    "schwaches": "weak",
    "selbst": "itself",
    "sein": "be",
    "seinem": "its",
    "sich": "itself",
    "sind": "are",
    "sofort": "immediately",
    "solange": "while",
    "sonst": "otherwise",
    "spaeter": "later",
    "steht": "is stored",
    "still": "silently",
    "taucht": "appears",
    "traegt": "carries",
    "ueber": "through",
    "ueberholt": "exceeds",
    "ueberleben": "outlive",
    "ueberlebt": "survives",
    "um": "to",
    "umginge": "would bypass",
    "unbekannt": "unknown",
    "unbekannte": "unknown",
    "unbrauchbar": "unusable",
    "unterscheiden": "distinguish",
    "unveraendert": "unchanged",
    "verarbeitet": "processed",
    "verbraucht": "consumed",
    "verliert": "loses",
    "verraet": "reveals",
    "verschiebt": "moves",
    "verschlossen": "closed",
    "vermutet": "often suspects",
    "verraten": "reveal",
    "verwendet": "used",
    "von": "from",
    "vor": "before",
    "vorher": "beforehand",
    "vorhanden": "present",
    "waere": "would be",
    "wann": "when",
    "warum": "why",
    "wenn": "when",
    "wer": "who",
    "wieder": "again",
    "wird": "is",
    "werden": "are",
    "wo": "where",
    "wohlgeformt": "well-formed",
    "wuerde": "would",
    "zaehlt": "counts",
    "zeigt": "shows",
    "zu": "to",
    "zusaetzlichen": "additional",
    "zwischen": "between",
    "zur": "to the",
    "zurueck": "back",
    "zuruecksetzt": "resets",
    "zum": "to the",
}

PHRASES = (
    ("wer sein passwort aendert, vermutet oft einen fremden zugriff", "a password change often indicates suspected unauthorized access"),
    ("ein unterschied waere ein weg, konten aufzuzaehlen", "a difference would enable account enumeration"),
    ("sonst koennte sich auf einer privaten instanz anlegen, wer ihre", "otherwise anyone who can reach a private instance could create an account"),
    ("die magic bytes entscheiden", "the magic bytes decide"),
    ("es gibt keine route, die einen storage key entgegennimmt", "no route accepts a storage key"),
    ("solange nichts gebunden ist, gibt es keinen parent, der traegt", "while nothing is bound, there is no parent that grants access"),
    ("ein 403 wuerde bestaetigen, dass es den space gibt", "a 403 would confirm that the space exists"),
    ("wohlgeformtheit darf keine existenzauskunft sein", "well-formedness must not disclose existence"),
    ("ein fehlender kopf ist der stille weg, den konfliktschutz abzuschalten", "a missing header is the silent path to disabling conflict protection"),
    ("eine neue operation ohne eintrag in dieser datei macht die suite rot", "a new operation without an entry in this file makes the suite fail"),
    ("die gegenprobe: sie sind der weg zu einem token und bleiben offen", "the countercheck: these endpoints lead to a token and remain public"),
    ("in der adresse steht nur die challenge, nie der verifier", "the URL contains only the challenge, never the verifier"),
    ("mehrere anbieter nebeneinander, nur ueber konfiguration", "multiple providers coexist through configuration only"),
    ("auch der externe weg endet in der zentralen sitzungsausgabe", "the external flow also ends in the central session issuance path"),
    ("sonst umginge ein externer anbieter die einladungsgrenze", "otherwise an external provider would bypass the invitation boundary"),
    ("jede einzelne pruefung, jeweils fuer sich", "each validation is tested independently"),
    ("ohne diese bindung liesse sich ein anderswo erbeutetes token einspielen", "without this binding, a token captured elsewhere could be replayed"),
    ("ein state gehoert zu genau einer verbindung", "a state belongs to exactly one connection"),
    ("sonst zeigte ein dokument unter erwarteter adresse auf fremde endpunkte", "otherwise a document at the expected URL could point to foreign endpoints"),
    ("die letzte grenze liegt im schema, nicht nur im dienst", "the final boundary is enforced by the schema, not only by the service"),
    ("die letzte grenze liegt im fremdschluessel, nicht nur im dienst", "the final boundary is enforced by the foreign key, not only by the service"),
    ("eine zahl ist selbst schon eine auskunft", "a count is itself a disclosure"),
    ("nicht laden und danach ausfiltern", "do not load first and filter afterwards"),
    ("wer die datenbank liest, darf sich damit nicht anmelden koennen", "database read access must not provide reusable sign-in credentials"),
    ("sonst liefe ein gestohlenes geraet noch bis zum ablauf weiter", "otherwise a stolen device would remain usable until token expiry"),
    ("unbekannt, abgelaufen und als replay erkannt sehen gleich aus", "unknown, expired, and replayed tokens must look identical"),
    ("die replay-historie darf keine zweite quelle fuer anmeldenachweise sein", "replay history must not become a second source of sign-in credentials"),
    ("nur ein echter token der familie loest den widerruf aus", "only a genuine token from the family may trigger revocation"),
    ("die familie hat eine harte obergrenze", "the session family has a hard lifetime limit"),
    ("der tokenwert wechselt bei jeder rotation - der zaehler nicht", "the token value changes on each rotation; the counter does not"),
    ("eine 429 darf nicht zur auskunft werden, dass es eine sitzung gibt", "a 429 must not disclose that a session exists"),
    ("sonst liefe ein tippfehler still als ungefilterte liste durch", "otherwise a typo would silently produce an unfiltered list"),
    ("gemeinsames schreiben heisst nicht: zwei getrennte versionsspuren", "shared writes do not create separate version histories"),
    ("ein veralteter stand darf keine fachliche auskunft erzeugen", "a stale version must not reveal domain state"),
)

WORD_PATTERN = re.compile(r"\b(" + "|".join(sorted(map(re.escape, WORDS), key=len, reverse=True)) + r")\b", re.IGNORECASE)


def _preserve_case(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


def translate_prose(text: str) -> str:
    prefix = ""
    body = text
    if body.startswith("#"):
        prefix = "#"
        body = body[1:]

    # Prefer complete phrases where the rationale is security- or
    # privacy-sensitive; fall back to the glossary for ordinary prose.
    lowered = body.lower()
    for source, target in PHRASES:
        if source in lowered:
            pattern = re.compile(re.escape(source), re.IGNORECASE)
            body = pattern.sub(target, body)
            lowered = body.lower()

    def replace(match: re.Match[str]) -> str:
        source = match.group(0)
        target = WORDS.get(source)
        if target is None:
            target = WORDS.get(source.lower())
        if target is None:
            # WORD_PATTERN is case-insensitive; locate the canonical key.
            for key, value in WORDS.items():
                if key.lower() == source.lower():
                    target = value
                    break
        assert target is not None
        return _preserve_case(source, target)

    body = WORD_PATTERN.sub(replace, body)
    body = body.replace(" - ", "; ")
    body = re.sub(r"\s+([,.;:])", r"\1", body)
    return prefix + body


def translate_identifier(name: str) -> str:
    exact = EXACT_IDENTIFIERS.get(name)
    if exact is not None:
        return exact

    parts = name.split("_")
    changed = False
    translated: list[str] = []
    for part in parts:
        replacement = SEGMENTS.get(part)
        if replacement is None:
            translated.append(part)
        else:
            translated.extend(replacement.split("_"))
            changed = True
    return "_".join(translated) if changed else name


def engineering_string_ranges(tree: ast.AST) -> set[tuple[int, int, int, int]]:
    ranges: set[tuple[int, int, int, int]] = set()

    def add_string_node(node: ast.AST | None) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            ranges.add((node.lineno, node.col_offset, node.end_lineno or node.lineno, node.end_col_offset or 0))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr):
                add_string_node(body[0].value)
        elif isinstance(node, ast.Assert):
            add_string_node(node.msg)
        elif isinstance(node, ast.Raise):
            if isinstance(node.exc, ast.Call):
                for argument in node.exc.args:
                    add_string_node(argument)
                for keyword in node.exc.keywords:
                    add_string_node(keyword.value)
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else None
            method = node.func.attr if isinstance(node.func, ast.Attribute) else None
            diagnostic = name in {"print", "fail", "skip", "xfail"} or method in {
                "debug",
                "info",
                "warning",
                "error",
                "exception",
                "critical",
            }
            if diagnostic:
                for argument in node.args:
                    add_string_node(argument)
                for keyword in node.keywords:
                    add_string_node(keyword.value)
            if method == "raises":
                for keyword in node.keywords:
                    if keyword.arg == "match":
                        add_string_node(keyword.value)
    return ranges


def _in_range(token: tokenize.TokenInfo, ranges: set[tuple[int, int, int, int]]) -> bool:
    sl, sc = token.start
    el, ec = token.end
    return any(sl >= rsl and el <= rel and (sl > rsl or sc >= rsc) and (el < rel or ec <= rec) for rsl, rsc, rel, rec in ranges)


def _rewrite_string_literal(token_text: str) -> str:
    try:
        value = ast.literal_eval(token_text)
    except (SyntaxError, ValueError):
        return token_text
    if not isinstance(value, str):
        return token_text
    translated = translate_prose(value)
    if translated == value:
        return token_text
    if "\n" in translated:
        escaped = translated.replace('"""', '\\"\\"\\"')
        return f'"""{escaped}"""'
    escaped = translated.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def migrate(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    tree = ast.parse(original)
    string_ranges = engineering_string_ranges(tree)

    output: list[tokenize.TokenInfo] = []
    for token in tokenize.generate_tokens(io.StringIO(original).readline):
        replacement = token.string
        if token.type == tokenize.NAME:
            replacement = translate_identifier(token.string)
        elif token.type == tokenize.COMMENT:
            replacement = translate_prose(token.string)
        elif token.type == tokenize.STRING and _in_range(token, string_ranges):
            replacement = _rewrite_string_literal(token.string)
        output.append(token._replace(string=replacement))

    rewritten = tokenize.untokenize(output)
    if rewritten != original:
        path.write_text(rewritten, encoding="utf-8")
        print(f"migrated {path}")


def main() -> int:
    for path in TARGETS:
        migrate(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
