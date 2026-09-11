"""Farbeingaben auf eine Form bringen.

Colors stehen in Einstellungsdateien und kommen aus Farbwaehlern, Textfeldern
und alten Staenden. Eine kaputte Farbe darf nirgends etwas sprengen - deshalb
gibt es hier immer einen brauchbaren Wert zurueck, notfalls den Rueckfall.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

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


def readable_on(hintergrund: str) -> str:
    """Schwarz oder Weiss - was auf dieser Flaeche besser lesbar ist.

    Fuer Schrift, die auf einer farbigen Flaeche steht: Auswahlbalken,
    Abzeichen, nummerierte Punkte. Ein fest eingetragenes Weiss traegt nur
    so lange, wie die Flaeche dunkel genug bleibt - bei einem gelben oder
    hellgruenen Akzent verschwindet es.

    Nicht ueber `is_light()`, sondern ueber den tatsaechlichen Kontrast:
    die YIQ-Naeherung dort hat eine feste Schwelle, hier entscheidet, was
    messbar besser traegt.

    Args:
        hintergrund:
            Die Flaeche, auf der die Schrift steht.

    Returns:
        '#000000' oder '#FFFFFF'.
    """
    return "#000000" if contrast_ratio("#000000", hintergrund) >= contrast_ratio("#FFFFFF", hintergrund) else "#FFFFFF"


def blend(grund: str, zumischung: str, anteil: float) -> str:
    """Mischt zwei Farben.

    Args:
        grund:
            Die Ausgangsfarbe.
        zumischung:
            Was hineingemischt wird.
        anteil:
            Wie viel davon, zwischen 0 und 1. Werte ausserhalb werden
            begrenzt, damit ein Rechenfehler an anderer Stelle nicht in
            eine unsinnige Farbe muendet.

    Returns:
        Die Mischfarbe als '#RRGGBB'.
    """
    gewicht = max(0.0, min(1.0, anteil))
    a = normalize(grund)
    b = normalize(zumischung)
    kanaele = []
    for stelle in (0, 2, 4):
        von = int(a[stelle : stelle + 2], 16)
        nach = int(b[stelle : stelle + 2], 16)
        kanaele.append(round(von + (nach - von) * gewicht))
    return "#" + "".join(f"{max(0, min(255, k)):02X}" for k in kanaele)


def ensure_contrast(farbe: str, hintergrund: str, ziel: float, *, schritte: int = 24) -> str:
    """Hellt eine Farbe auf oder dunkelt sie ab, bis sie ihr Ziel erreicht.

    Die Richtung ergibt sich aus dem Hintergrund: auf dunklem Grund wird zu
    Weiss hin gemischt, auf hellem zu Schwarz. Erreicht die Farbe ihr Ziel
    schon, bleibt sie unveraendert - das ist der Normalfall und der Grund,
    warum ein Theme seinen Charakter behaelt.

    Args:
        farbe:
            Die gewuenschte Farbe.
        hintergrund:
            Die Flaeche, auf der sie steht.
        ziel:
            Das Mindestkontrastverhaeltnis.
        schritte:
            Wie fein gesucht wird. Mehr Schritte heisst eine Farbe, die
            naeher am Original liegt.

    Returns:
        Die naechstgelegene Farbe, die das Ziel erreicht. Ist es auch mit
        reinem Weiss oder Schwarz nicht zu erreichen, kommt dieses zurueck -
        besser der bestmoegliche Kontrast als der zu schwache Ausgangswert.
    """
    if contrast_ratio(farbe, hintergrund) >= ziel:
        return f"#{normalize(farbe)}"

    pol = "#FFFFFF" if relative_luminance(hintergrund) < 0.5 else "#000000"
    for schritt in range(1, schritte + 1):
        kandidat = blend(farbe, pol, schritt / schritte)
        if contrast_ratio(kandidat, hintergrund) >= ziel:
            return kandidat
    return pol


def ensure_contrast_on_all(farbe: str, hintergruende: Sequence[str], ziel: float) -> str:
    """Wie `ensure_contrast`, aber gegen mehrere Flaechen zugleich.

    Der Regelfall in einer Oberflaeche: derselbe Text steht mal auf dem
    Fenstergrund, mal auf einer Karte, mal auf einer Schaltflaeche. Wer nur
    gegen den Fenstergrund prueft, bekommt eine falsche Entwarnung - genau
    daran lag der Kontrastmangel, der bis zum 10.09.2026 in dieser
    Bibliothek stand.

    Args:
        farbe:
            Die gewuenschte Farbe.
        hintergruende:
            Alle Flaechen, auf denen sie vorkommen kann.
        ziel:
            Das Mindestkontrastverhaeltnis, das auf JEDER gelten soll.

    Returns:
        Die Farbe, angehoben bis sie ihr Ziel auf der unguenstigsten
        Flaeche erreicht.
    """
    if not hintergruende:
        return f"#{normalize(farbe)}"

    ergebnis = f"#{normalize(farbe)}"
    # Nacheinander gegen jede Flaeche heben und das Ergebnis weiterreichen:
    # eine Anhebung fuer die eine Flaeche kann den Kontrast zu einer anderen
    # senken, deshalb am Ende noch eine Runde zur Kontrolle.
    for _ in range(2):
        for grund in hintergruende:
            ergebnis = ensure_contrast(ergebnis, grund, ziel)
        if min(contrast_ratio(ergebnis, g) for g in hintergruende) >= ziel:
            break
    return ergebnis


def relative_luminance(hexwert: str) -> float:
    """Die relative Leuchtdichte nach WCAG 2.1.

    Bewusst nicht dieselbe Formel wie `is_light`: die dort verwendete
    YIQ-Naeherung rechnet auf den rohen Kanalwerten. WCAG entzerrt sie
    vorher (Gamma), und nur damit ergibt das Kontrastverhaeltnis die
    Zahlen, gegen die Barrierefreiheitsvorgaben formuliert sind.

    Args:
        hexwert:
            Die Farbe in einer der von `normalize` verstandenen Formen.

    Returns:
        Ein Wert zwischen 0 (Schwarz) und 1 (Weiß).
    """
    roh = normalize(hexwert)
    kanaele = []
    for stelle in (0, 2, 4):
        anteil = int(roh[stelle : stelle + 2], 16) / 255
        kanaele.append(anteil / 12.92 if anteil <= 0.04045 else ((anteil + 0.055) / 1.055) ** 2.4)
    return 0.2126 * kanaele[0] + 0.7152 * kanaele[1] + 0.0722 * kanaele[2]


def contrast_ratio(vorne: str, hinten: str) -> float:
    """Das Kontrastverhaeltnis zweier Farben nach WCAG 2.1.

    Die Schwellen, gegen die man das misst: 4.5 für Fließtext, 3.0 für große
    Schrift und grafische Elemente. Eine reine Trennlinie muss sich nur
    absetzen, dort genügt weniger.

    Args:
        vorne:
            Die Farbe im Vordergrund - Schrift, Linie, Sinnbild.
        hinten:
            Die Fläche darunter.

    Returns:
        Ein Wert zwischen 1.0 (nicht zu unterscheiden) und 21.0 (Schwarz
        auf Weiß). Die Reihenfolge der Argumente ändert das Ergebnis nicht.
    """
    hell, dunkel = sorted((relative_luminance(vorne), relative_luminance(hinten)), reverse=True)
    return (hell + 0.05) / (dunkel + 0.05)
