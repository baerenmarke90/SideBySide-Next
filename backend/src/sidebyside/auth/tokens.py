"""Token-Erzeugung und -Pruefung.

Bewusst undurchsichtige Zufallstoken statt JWT.

Der ueblliche Vorteil eines JWT ist, dass der Server ihn ohne
Datenbankzugriff pruefen kann. Dieser Vorteil greift hier nicht: jede
Anfrage auf Space-Daten muss ohnehin die Mitgliedschaft nachschlagen. Ein
zusaetzlicher indizierter Zugriff kostet also praktisch nichts.

Dafuer bringt der undurchsichtige Token zwei Eigenschaften mit, die bei
einem privaten Paar-Dienst schwerer wiegen als die eingesparte Abfrage:

- Widerruf wirkt sofort. Ein JWT bleibt bis zum Ablauf gueltig, auch wenn
  das Geraet als gestohlen gemeldet wurde.
- Es gibt keinen Signaturschluessel, der rotiert, verteilt und geschuetzt
  werden muss.

Gespeichert wird nur der Hash. Ein Token hat volle Entropie aus
`secrets.token_urlsafe`, deshalb genuegt SHA-256 - es gibt kein Woerterbuch,
gegen das sich das angreifen liesse, und ein langsames Verfahren wie bcrypt
waere hier nur eine Bremse bei jeder Anfrage.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

ACCESS_TOKEN_BYTES = 32
REFRESH_TOKEN_BYTES = 32

ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)

# Gleitendes Fenster: jede Rotation setzt es neu. Es begrenzt, wie lange ein
# Geraet unbenutzt liegen darf, bevor es sich neu anmelden muss.
REFRESH_TOKEN_LIFETIME = timedelta(days=60)

# Harte Obergrenze der Sitzung, gerechnet ab der Anmeldung und bei keiner
# Rotation verlaengert.
#
# Ohne sie ist die Sitzungsdauer unbegrenzt: wer regelmaessig erneuert,
# schiebt das gleitende Fenster beliebig weit vor sich her. Damit waere
# weder die Familie noch ihre Replay-Historie nach oben beschraenkt, und
# ein einmal gestohlenes Geraet bliebe dauerhaft angemeldet.
#
# Nach Ablauf hilft keine Rotation mehr; es braucht eine neue Anmeldung und
# damit eine neue Token-Familie.
SESSION_ABSOLUTE_LIFETIME = timedelta(days=180)


def generate_token(size: int = ACCESS_TOKEN_BYTES) -> str:
    """Ein neues Geheimnis. Nur der Aufrufer bekommt es je zu sehen."""
    return secrets.token_urlsafe(size)


def hash_token(token: str) -> str:
    """Der Hash, wie er persistiert wird."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_equal(left: str, right: str) -> bool:
    """Zeitkonstanter Vergleich zweier Hashes.

    Ein Vergleich mit `==` bricht beim ersten abweichenden Zeichen ab. Aus
    der Laufzeit laesst sich dann Zeichen fuer Zeichen ein gueltiger Wert
    erraten.
    """
    return secrets.compare_digest(left, right)
