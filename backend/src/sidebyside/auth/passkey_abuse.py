"""Abuse-Grenze fuer den anonymen Start einer Passkey-Anmeldung.

Der Start einer WebAuthn-Authentifizierung kennt absichtlich weder Konto noch
Credential. Als Rate-Limit-Schluessel bleibt deshalb nur die bereits an der
HTTP-Grenze vertrauenswuerdig aufgeloeste Netzwerkidentitaet des Clients.

`request.client.host` kommt in Produktion aus dem von Uvicorn bereinigten ASGI-
Scope. Forwarded-Header werden dort nur fuer die explizit konfigurierten
`FORWARDED_ALLOW_IPS` ausgewertet. Dieses Modul parst deshalb bewusst weder
`Forwarded` noch `X-Forwarded-For` selbst.
"""

from __future__ import annotations

from datetime import timedelta
from ipaddress import IPv6Address, ip_address, ip_network

from sqlalchemy.orm import Session

from sidebyside.auth import rate_limit

ACTION_AUTHENTICATION_START = "passkey_auth_start"
AUTHENTICATION_START = rate_limit.Limit(attempts=30, window=timedelta(minutes=15))
"""Grosszuegiges Human-Budget, aber begrenzter Challenge-Schreibdurchsatz.

30 Starts in 15 Minuten liegen deutlich ueber einem normalen interaktiven
Login-Flow. Die Grenze gilt pro Netzwerkidentitaet statt global, damit ein
Angreifer nicht mit einem einzigen Schluessel alle Passkey-Anmeldungen der
Instanz blockieren kann.
"""


def network_key(client_host: str | None) -> str:
    """Stabilen, nicht accountbezogenen Abuse-Key aus dem ASGI-Peer ableiten.

    IPv4 wird einzeln begrenzt. IPv6 wird auf /64 normalisiert, damit ein
    Client die Grenze nicht durch Rotation der Interface-ID im selben Netz
    umgehen kann. IPv4-mapped IPv6 wird wie IPv4 behandelt.

    Der Rueckfall fuer nicht-IP-basierte ASGI-Test-/Transport-Clients bleibt
    absichtlich an deren Peer-Bezeichner gebunden. In einem produktiven TCP-
    Deployment liefert Uvicorn hier eine IP-Adresse.
    """
    raw = (client_host or "unknown").strip().lower() or "unknown"
    try:
        address = ip_address(raw)
    except ValueError:
        return f"peer:{raw}"

    if isinstance(address, IPv6Address):
        if address.ipv4_mapped is not None:
            return f"ipv4:{address.ipv4_mapped.compressed}"
        network = ip_network((address, 64), strict=False)
        return f"ipv6:{network.network_address.compressed}/64"

    return f"ipv4:{address.compressed}"


def reserve_authentication_start(session: Session, client_host: str | None) -> None:
    """Vor jedem Challenge-Write atomar einen DB-weiten Slot reservieren."""
    key = network_key(client_host)
    rate_limit.check(session, ACTION_AUTHENTICATION_START, key, AUTHENTICATION_START)
    # Historische Aufrufer-Semantik beibehalten. Seit #60 erkennt
    # `record_attempt`, dass `check` den Slot bereits persistent reserviert
    # hat, und erzeugt deshalb keinen zweiten Event.
    rate_limit.record_attempt(session, ACTION_AUTHENTICATION_START, key)
