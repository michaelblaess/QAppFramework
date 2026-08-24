"""Farbeingaben auf eine Form bringen.

Colors stehen in Einstellungsdateien und kommen aus Farbwaehlern, Textfeldern
und alten Staenden. Eine kaputte Farbe darf nirgends etwas sprengen - deshalb
gibt es hier immer einen brauchbaren Wert zurueck, notfalls den Rueckfall.
"""

from __future__ import annotations

import re

STANDARDFARBE = "FF0000"

_SECHSSTELLIG = re.compile(r"^[0-9A-Fa-f]{6}$")
_DREISTELLIG = re.compile(r"^[0-9A-Fa-f]{3}$")
_TRIPEL = re.compile(r"^(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})$")


def normalize(wert: str, rueckfall: str = STANDARDFARBE) -> str:
    """Bringt eine Farbeingabe auf RRGGBB in Grossbuchstaben.

    Akzeptiert '#RRGGBB', 'RRGGBB', die Kurzform '#RGB' und ein Tripel wie
    '255,0,0'.

    Args:
        wert:
            Die Eingabe.
        rueckfall:
            Was bei einer unbrauchbaren Eingabe herauskommt.

    Returns:
        Sechs Hexstellen ohne fuehrendes Doppelkreuz.
    """
    roh = (wert or "").strip().lstrip("#").strip()
    if _SECHSSTELLIG.match(roh):
        return roh.upper()
    if _DREISTELLIG.match(roh):
        return "".join(zeichen * 2 for zeichen in roh).upper()
    treffer = _TRIPEL.match(roh)
    if treffer:
        werte = [int(teil) for teil in treffer.groups()]
        if all(0 <= teil <= 255 for teil in werte):
            return "".join(f"{teil:02X}" for teil in werte)
    return rueckfall.strip().lstrip("#").upper() if rueckfall else STANDARDFARBE


def is_light(hexwert: str) -> bool:
    """Ob auf dieser Farbe schwarze Schrift besser lesbar ist als weisse.

    Ueber die wahrgenommene Helligkeit, nicht ueber den Mittelwert der Kanaele:
    Gruen wirkt deutlich heller als Blau, obwohl beide denselben Zahlenwert
    haben koennen.
    """
    roh = normalize(hexwert)
    rot, gruen, blau = (int(roh[i : i + 2], 16) for i in (0, 2, 4))
    return (0.299 * rot + 0.587 * gruen + 0.114 * blau) > 150
