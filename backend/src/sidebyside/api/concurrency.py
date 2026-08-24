"""Optimistic Concurrency an der HTTP-Grenze.

Die Version einer Ressource geht als ETag hinaus und als `If-Match` wieder
herein. Damit steht die Konfliktpruefung dort, wo HTTP sie ohnehin vorsieht,
und nicht als Sonderfeld in jedem einzelnen Anfragekoerper.

Ein Schreibzugriff ohne `If-Match` wird abgelehnt statt stillschweigend
durchgelassen. Ein fehlender Kopf ist sonst genau der Weg, auf dem ein
Client den Konfliktschutz versehentlich abschaltet - und der Lost Update
faellt niemandem auf.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header

from sidebyside.core.errors import ErrorCode, ValidationError


def etag_for(version: int) -> str:
    """Die Version als starkes ETag."""
    return f'"{version}"'


def parse_if_match(value: str) -> int:
    """Aus dem `If-Match`-Kopf die erwartete Version lesen.

    Akzeptiert wird genau ein starkes ETag - mit oder ohne
    Anfuehrungszeichen, weil beide Schreibweisen in freier Wildbahn
    vorkommen.

    Ein leerer Wert zaehlt wie ein unbrauchbarer: er benennt keine Version.

    Ausdruecklich nicht akzeptiert:

    - `*`, das nur "irgendeine vorhandene Darstellung" bedeutet und den
      Konfliktschutz damit aufheben wuerde,
    - schwache Validatoren `W/"..."`, die fuer `If-Match` ohnehin
      unzulaessig sind,
    - mehrere Werte, weil eine Ressource genau eine Version hat.
    """
    roh = value.strip()
    if roh.startswith('"') and roh.endswith('"') and len(roh) >= 2:
        roh = roh[1:-1]

    if not (roh.isascii() and roh.isdigit()):
        raise ValidationError(
            "The If-Match header must carry a single concrete version.",
            ErrorCode.IF_MATCH_MALFORMED,
        )

    return int(roh)


def if_match_version(
    if_match: Annotated[
        str,
        Header(
            alias="If-Match",
            description=(
                "Die zuletzt gelesene Version der Ressource, als starkes ETag. "
                "Ohne diesen Kopf wird nicht geschrieben."
            ),
        ),
    ],
) -> int:
    """Pflichtkopf.

    Ausdruecklich ohne Standardwert: so steht er auch im OpenAPI-Vertrag als
    Pflicht. Ein Vertrag, der ihn als optional fuehrt, waere eine Einladung,
    ihn wegzulassen - und genau das schaltet den Konfliktschutz ab.
    """
    return parse_if_match(if_match)


IfMatchVersion = Annotated[int, Depends(if_match_version)]
