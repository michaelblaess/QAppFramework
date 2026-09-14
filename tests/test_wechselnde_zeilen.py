"""Wechselnde Tabellenzeilen muessen sich sichtbar abheben - in jedem Theme.

Bis zum 14.09.2026 war die zweite Zeile fest bg_secondary. Gemessen lag der
Kontrast zur normalen Zeile bei 39 von 40 Themes zwischen 1,03 und 1,06:1.
Aufgefallen bei Bunty, Minty, BeBox, Ascot und Metropolis - betroffen waren
fast alle.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Die Palette gehoert zur Desktop-Oberflaeche")

from PySide6.QtGui import QPalette  # noqa: E402

from QAppFramework.color import contrast_ratio  # noqa: E402
from QAppFramework.derive import available_themes, colors_from_palette, palette_for_theme  # noqa: E402
from QAppFramework.theme import (  # noqa: E402
    ALTERNATE_ROW_CONTRAST,
    DARK,
    LIGHT,
    ROW_TEXT_CONTRAST,
    Colors,
    alternate_row_color,
    build_palette,
)


def _paletten() -> list[tuple[str, Colors]]:
    paletten = [("grund-dunkel", DARK), ("grund-hell", LIGHT)]
    for name in available_themes():
        roh = palette_for_theme(name)
        assert roh is not None
        paletten.append((name, Colors(**colors_from_palette(roh), expressive=True)))
    return paletten


PALETTEN = _paletten()


# Das Ziel ist ALTERNATE_ROW_CONTRAST. Wo der Fliesstext dafuer unter seine
# Grenze fiele, hat die Lesbarkeit Vorrang - gemessen am 14.09.2026 betrifft
# das nur Motif (1,177). Sichtbar abheben muss sich die Zeile trotzdem: der
# alte Stand lag bei 1,03 bis 1,06.
MINDESTENS_SICHTBAR = 1.15


@pytest.mark.parametrize(("name", "farben"), PALETTEN, ids=[name for name, _ in PALETTEN])
def test_die_zweite_zeile_hebt_sich_ab(name: str, farben: Colors) -> None:
    zeile = alternate_row_color(farben)
    assert contrast_ratio(zeile, farben.bg_tertiary) >= MINDESTENS_SICHTBAR, (name, zeile)


def test_bei_motif_begrenzt_die_lesbarkeit_das_ziel() -> None:
    """Der eine Fall, in dem das Ziel nicht erreicht wird - und warum."""
    roh = palette_for_theme("motif")
    assert roh is not None
    farben = Colors(**colors_from_palette(roh), expressive=True)
    zeile = alternate_row_color(farben)
    assert contrast_ratio(zeile, farben.bg_tertiary) < ALTERNATE_ROW_CONTRAST
    assert contrast_ratio(farben.text_primary, zeile) >= ROW_TEXT_CONTRAST


@pytest.mark.parametrize(("name", "farben"), PALETTEN, ids=[name for name, _ in PALETTEN])
def test_der_text_bleibt_darauf_lesbar(name: str, farben: Colors) -> None:
    zeile = alternate_row_color(farben)
    assert contrast_ratio(farben.text_primary, zeile) >= ROW_TEXT_CONTRAST, (name, zeile)


@pytest.mark.parametrize(
    "name", ["bunty", "minty", "bebox", "ascot", "metropolis"], ids=lambda name: name
)
def test_die_gemeldeten_themes(name: str) -> None:
    """Die fuenf, an denen es aufgefallen ist, ausdruecklich."""
    roh = palette_for_theme(name)
    assert roh is not None
    farben = Colors(**colors_from_palette(roh), expressive=True)
    assert contrast_ratio(alternate_row_color(farben), farben.bg_tertiary) >= ALTERNATE_ROW_CONTRAST


def test_die_palette_nutzt_die_abgeleitete_farbe() -> None:
    """Sonst gilt die Rechnung, und die Tabelle zeigt trotzdem das Alte."""
    farbe = build_palette(DARK).color(QPalette.ColorRole.AlternateBase).name().lower()
    assert farbe == alternate_row_color(DARK).lower()
