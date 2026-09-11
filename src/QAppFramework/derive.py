"""Baut aus einem Terminal-Theme eine vollstaendige Qt-Palette.

Ein Theme aus `textual-themes` traegt elf Grundfarben, `Colors` hat sechzehn
Felder. Fuenf davon werden hier abgeleitet, und zwar nach Anteilen, die aus
der Bestandspalette dieser Bibliothek zurueckgerechnet wurden - nicht nach
Gefuehl. Die Messung steht im Skill `qt-specialist`.

Der Ablauf hat zwei Stufen, und die zweite ist die wichtige:

1. Die Rohableitung mischt jede abgeleitete Farbe aus Grund und Schrift.
2. Danach wird jede Rolle auf ihr Kontrastziel gehoben - gegen JEDEN der
   vier Flaechentoene, nicht nur gegen den Fenstergrund.

Ohne Stufe 2 sieht ein Theme auf dem Fenstergrund gut aus und faellt
ueberall dort auseinander, wo eine andere Flaeche darunter liegt. Genau das
war am ersten Versuch zu sehen: der Fliesstext trug, die inaktiven Reiter
auf `bg_secondary` blieben blass.

Public API:
    - `colors_from_palette()` - die Umrechnung.
    - `available_themes()` - Name und Anzeigename aller Themes.
    - `palette_for_theme()` - ein Theme ueber seinen Namen.

Dieses Modul haengt an den **Daten** von textual-themes, nicht an Textual.
Das Extra wird bewusst nicht gezogen (siehe pyproject.toml).
"""

from __future__ import annotations

from textual_themes.palettes import (
    DISPLAY_NAMES,
    PALETTES_BY_NAME,
    RETRO_PALETTES,
    Palette,
)

from .color import blend, contrast_ratio, ensure_contrast_on_all

# ── Die Mischanteile ──────────────────────────────────────────────────
#
# Zurueckgerechnet aus DARK und LIGHT: fuer jedes Feld der Anteil, der
# blend(Grund, Schrift, a) am naechsten an den Bestandswert bringt. Die
# Bestandspalette ist damit fast vollstaendig beschreibbar - groesster
# Restfehler 11 auf einer Skala bis 441.
#
# Je Erscheinungsbild getrennt, weil die Flaechentreppe sich unterscheidet:
# im Dunkelmodus steigt sie monoton, im Hellmodus ist die Tabelle
# Papierweiss und damit heller als der Fenstergrund, waehrend Panels und
# Schaltflaechen dunkler sind.
ANTEILE_DUNKEL: dict[str, float] = {
    "bg_secondary": 0.023,
    "bg_tertiary": 0.034,
    "bg_elevated": 0.090,
    "border": 0.151,
    "border_hover": 0.243,
    "text_secondary": 0.656,
    "text_tertiary": 0.432,
}
ANTEILE_HELL: dict[str, float] = {
    "bg_secondary": 0.017,
    "bg_elevated": 0.035,
    "border": 0.138,
    "border_hover": 0.253,
    "text_secondary": 0.660,
    "text_tertiary": 0.457,
}

# Im Hellmodus setzt sich die Arbeitsflaeche nach oben ab statt nach unten.
# 0.35 statt 1.0, damit ein Elfenbein-Theme nicht auf reines Weiss springt
# und seinen Charakter verliert.
HELL_TABELLE_AUFHELLUNG = 0.35

# Wie weit sich die Flaechen voneinander abheben muessen.
#
# Die Mischanteile oben sind aus der Grundpalette zurueckgerechnet, deren
# Grund schon aufgehellt ist. Bei einem fast schwarzen Theme ergeben 2,3
# Prozent praktisch nichts: gemessen kamen alle 40 Schemata auf 1,03 bis
# 1,07 zwischen Fenstergrund und Panel, also unter jede Wahrnehmungs-
# schwelle. Sichtbar wurde das an einem Dialog, der im Hintergrund verschwand.
#
# Die Zielwerte sind nicht erfunden, sondern das, was die Grundpalette
# erreicht - sie ist der Beleg dafuer, dass es traegt.
# Je Erscheinungsbild getrennt, wie die Mischanteile auch. Ein Ziel von
# 1.25 fuer die Schaltflaeche taugt nur im Dunkelmodus: auf hellem Grund
# hiesse das deutlich dunkler, und dann findet sich keine Textfarbe mehr,
# die auf Fenstergrund UND Schaltflaeche traegt. Der Test an "brick" hat
# genau das gezeigt.
FLAECHEN_ZIELE_DUNKEL: dict[str, float] = {
    "bg_secondary": 1.05,
    "bg_tertiary": 1.09,
    "bg_elevated": 1.25,
}
FLAECHEN_ZIELE_HELL: dict[str, float] = {
    "bg_secondary": 1.035,
    "bg_tertiary": 1.09,
    "bg_elevated": 1.066,
}


def _abgesetzt(flaeche: str, grund: str, schrift: str, ziel: float) -> str:
    """Mischt eine Flaeche weiter zur Schrift, bis sie sich vom Grund abhebt.

    Zur Schrift und nicht zu Weiss: so behaelt die Flaeche den Farbton des
    Themes. Ein Bernstein-Monitor bekommt eine bernsteinfarbene Karte, kein
    graues Rechteck.

    Args:
        flaeche: Der Ausgangswert aus der Rohableitung.
        grund: Der Fenstergrund, gegen den sie sich absetzen soll.
        schrift: Die Textfarbe des Themes, Richtung der Mischung.
        ziel: Das Mindestkontrastverhaeltnis.

    Returns:
        Die abgesetzte Flaeche, oder den Ausgangswert wenn er schon reicht.
    """
    if contrast_ratio(flaeche, grund) >= ziel:
        return flaeche
    for schritt in range(1, 301):
        kandidat = blend(flaeche, schrift, schritt / 1000)
        if contrast_ratio(kandidat, grund) >= ziel:
            return kandidat
    return blend(flaeche, schrift, 0.3)

# ── Die Kontrastziele ─────────────────────────────────────────────────
#
# Dieselben Werte, gegen die `TestKontrast` die Bestandspalette prueft.
# 4.5 ist die WCAG-Schwelle fuer Fliesstext, 3.0 fuer grosse Schrift und
# grafische Elemente. 1.4 fuer die Linien ist keine WCAG-Zahl, sondern die
# Schwelle, ab der eine Trennlinie auf allen vier Flaechen sichtbar bleibt.
ZIELE: dict[str, float] = {
    "text_secondary": 4.5,
    "text_tertiary": 3.0,
    "accent": 3.0,
    "border": 1.4,
    "border_hover": 1.4,
    # Die Statusfarben sind Text in Tabellenzellen, kein Schmuck.
    "status": 4.5,
}

# Der Hover-Ton soll ueber der ruhenden Linie liegen, nicht daneben.
BORDER_HOVER_ZIEL_AUFSCHLAG = 0.4


def _rgba(hexwert: str, deckkraft: float) -> str:
    """Baut den rgba()-Ausdruck, den Qt im Stylesheet erwartet."""
    roh = hexwert.lstrip("#")
    rot, gruen, blau = (int(roh[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({rot}, {gruen}, {blau}, {deckkraft:.2f})"


def colors_from_palette(palette: Palette) -> dict[str, str]:
    """Rechnet die elf Grundfarben eines Themes in die sechzehn Qt-Felder um.

    Args:
        palette:
            Die Grundfarben aus `textual-themes`.

    Returns:
        Die Feldwerte als Abbildung, passend fuer `Colors(**werte)`. Bewusst
        ein Dict und keine `Colors`-Instanz: so bleibt dieses Modul frei von
        `theme.py` und damit von PySide6, und es laesst sich ohne Qt testen.
    """
    anteile = ANTEILE_DUNKEL if palette.dark else ANTEILE_HELL
    flaechenziele = FLAECHEN_ZIELE_DUNKEL if palette.dark else FLAECHEN_ZIELE_HELL
    grund = palette.background
    schrift = palette.foreground

    # Stufe 1 - die Flaechen. Sie sind der Bezug fuer alles Weitere und
    # werden deshalb nicht nachtraeglich veraendert.
    bg_primary = grund
    bg_secondary = _abgesetzt(
        blend(grund, schrift, anteile["bg_secondary"]), grund, schrift, flaechenziele["bg_secondary"]
    )
    bg_elevated = _abgesetzt(
        blend(grund, schrift, anteile["bg_elevated"]), grund, schrift, flaechenziele["bg_elevated"]
    )
    if palette.dark:
        bg_tertiary = _abgesetzt(
            blend(grund, schrift, anteile["bg_tertiary"]), grund, schrift, flaechenziele["bg_tertiary"]
        )
    else:
        # Im Hellmodus setzt sich die Tabelle nach oben ab - sie ist das
        # Papier, auf dem gelesen wird.
        bg_tertiary = blend(grund, "#FFFFFF", HELL_TABELLE_AUFHELLUNG)
        # Bei einem fast weissen Grund geht das nicht: plan9 startet bei
        # #FFFFEA, und Aufhellen bringt dort nichts mehr. Dann weicht die
        # Tabelle nach unten aus, statt im Fenster zu verschwinden.
        if contrast_ratio(bg_tertiary, grund) < flaechenziele["bg_tertiary"]:
            bg_tertiary = _abgesetzt(grund, grund, schrift, flaechenziele["bg_tertiary"])

    flaechen = (bg_primary, bg_secondary, bg_tertiary, bg_elevated)

    # Stufe 2 - jede Rolle auf ihr Ziel heben, gegen alle vier Flaechen.
    def gehoben(feld: str, roh: str, ziel: float | None = None) -> str:
        return ensure_contrast_on_all(roh, flaechen, ZIELE[feld] if ziel is None else ziel)

    border = gehoben("border", blend(grund, schrift, anteile["border"]))
    border_hover = gehoben(
        "border_hover",
        blend(grund, schrift, anteile["border_hover"]),
        ZIELE["border_hover"] + BORDER_HOVER_ZIEL_AUFSCHLAG,
    )

    accent = gehoben("accent", palette.accent)
    # Der Hover-Ton des Akzents geht zur Schrift hin und nicht pauschal ins
    # Helle - sonst kippt ein heller Akzent auf hellem Grund ins Unsichtbare.
    accent_hover = gehoben("accent", blend(accent, schrift, 0.25))

    return {
        "bg_primary": bg_primary,
        "bg_secondary": bg_secondary,
        "bg_tertiary": bg_tertiary,
        "bg_elevated": bg_elevated,
        "border": border,
        "border_hover": border_hover,
        "text_primary": schrift,
        "text_secondary": gehoben("text_secondary", blend(grund, schrift, anteile["text_secondary"])),
        "text_tertiary": gehoben("text_tertiary", blend(grund, schrift, anteile["text_tertiary"])),
        "accent": accent,
        "accent_hover": accent_hover,
        "accent_subtle": _rgba(accent, 0.20 if palette.dark else 0.14),
        # Die Statusfarben stehen als TEXT in Tabellenzellen - "erreichbar",
        # "nicht gefunden" - und brauchen deshalb dasselbe Ziel wie jede
        # andere Schrift. Bis zum 11.09.2026 kamen sie unveraendert aus dem
        # Theme, mit der Begruendung, ein Theme duerfe seine Toene behalten.
        # Gemessen verfehlten damit ALLE 40 Schemata das Ziel, und die beiden
        # Grundpaletten gleich mit: Rot fiel bei 32 von 40 durch, Violett bei
        # 24, Gruen bei 15. Michael ist es am Vergleich mit der TUI
        # aufgefallen, wo dieselbe Farbe deutlich kraeftiger wirkt.
        "green": gehoben("status", palette.success, ZIELE["status"]),
        "orange": gehoben("status", palette.warning, ZIELE["status"]),
        "red": gehoben("status", palette.error, ZIELE["status"]),
        "purple": gehoben("status", palette.secondary, ZIELE["status"]),
    }


def available_themes() -> dict[str, str]:
    """Alle waehlbaren Themes.

    Returns:
        Je Theme-Name der Anzeigename, alphabetisch nach Anzeigename. Der
        Schluessel steht in der Einstellungsdatei und aendert sich nicht.
    """
    return dict(sorted(DISPLAY_NAMES.items(), key=lambda paar: paar[1].lower()))


def palette_for_theme(name: str) -> Palette | None:
    """Sucht ein Theme ueber seinen Namen.

    Args:
        name:
            Der Theme-Name, wie er in der Einstellungsdatei steht.

    Returns:
        Die Palette, oder None bei einem unbekannten Namen. Kein Fehler:
        eine Einstellungsdatei kann aus einer aelteren Fassung stammen, und
        dann ist der Rueckfall auf die Standardpalette richtig.
    """
    return PALETTES_BY_NAME.get(name)


__all__ = [
    "RETRO_PALETTES",
    "Palette",
    "available_themes",
    "colors_from_palette",
    "palette_for_theme",
]
