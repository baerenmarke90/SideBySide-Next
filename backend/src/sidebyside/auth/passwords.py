"""Passwort-Ableitung.

Argon2id, der derzeitige Empfehlungsstandard. Anders als bei den Tokens ist
hier ein absichtlich langsames Verfahren richtig: ein Passwort hat wenig
Entropie und laesst sich sonst mit einem Woerterbuch durchprobieren.

Die einzige Stelle im Projekt, an der eine Kryptografie-Bibliothek noetig
ist. Tokens kommen mit der Standardbibliothek aus.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from sidebyside.core.errors import ValidationError

# Untergrenze gegen offensichtlich Schwaches. Keine Obergrenze fuer
# Zeichenklassen: Laenge schuetzt besser als erzwungene Sonderzeichen, die
# vor allem dazu fuehren, dass Leute "Passwort1!" waehlen.
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 4096

_hasher = PasswordHasher()


class PasswordErrorCode:
    TOO_SHORT = "PASSWORD_TOO_SHORT"
    TOO_LONG = "PASSWORD_TOO_LONG"


def validate(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"The password must be at least {MIN_PASSWORD_LENGTH} characters.",
            PasswordErrorCode.TOO_SHORT,
        )
    # Eine Obergrenze ist noetig: Argon2 arbeitet ueber die volle Eingabe,
    # ein sehr langes Passwort waere sonst ein billiger Weg, den Server zu
    # beschaeftigen.
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError("The password is too long.", PasswordErrorCode.TOO_LONG)


def hash_password(password: str) -> str:
    validate(password)
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Prueft das Passwort. Gibt False zurueck statt zu werfen.

    Ein fehlgeschlagener Anmeldeversuch ist ein erwarteter Fall, kein
    Fehler - und der Aufrufer soll nicht zwischen "falsches Passwort" und
    "kaputter Hash" unterscheiden muessen.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Ob der Hash mit veralteten Parametern erzeugt wurde.

    Werden die Parameter spaeter angehoben, wandern bestehende Passwoerter
    bei der naechsten erfolgreichen Anmeldung mit.
    """
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


DUMMY_HASH = _hasher.hash("nicht-echt-nur-zum-zeitausgleich")
"""Ein Hash zum Vergleichen, wenn es den Account gar nicht gibt.

Ohne ihn waere die Antwort bei unbekannter Adresse spuerbar schneller als
bei falschem Passwort - daraus liesse sich ablesen, welche Adressen
registriert sind.
"""
