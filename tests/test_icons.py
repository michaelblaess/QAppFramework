"""Jeder eingetragene Glyph muss sich auch zeichnen lassen.

`load_icon` gibt bei einem unbekannten Glyph ein leeres QIcon zurueck und
schreibt eine Warnung ins Protokoll - richtig so, eine fehlende Grafik darf
die Werkzeugleiste nicht verhindern. Der Preis ist, dass ein Tippfehler in
GLYPHS nirgends auffaellt: die Leiste zeigt dann eine Luecke, und niemand
sieht die Warnung.

Deshalb dieser Test. Er hat einen echten Anlass - beim Einbau der
Farbschema-Aktionen waren zwei neue Namen zu erfinden, und ob ein
mdi6-Glyph unter genau diesem Namen existiert, weiss man vorher nicht.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Sinnbilder gehoeren zur Desktop-Oberflaeche")

from PySide6.QtWidgets import QApplication  # noqa: E402

from QAppFramework.icons import GLYPHS, load_icon  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def anwendung() -> QApplication:
    """QtAwesome braucht eine laufende QApplication, um Schriften zu laden."""
    vorhanden = QApplication.instance()
    return vorhanden if isinstance(vorhanden, QApplication) else QApplication([])


class TestGlyphen:
    @pytest.mark.parametrize("name", sorted(GLYPHS))
    def test_jeder_name_liefert_ein_sichtbares_sinnbild(self, name: str) -> None:
        icon = load_icon(name, "#ffffff")
        assert not icon.isNull(), f"{name} ({GLYPHS[name]}) ergibt ein leeres Sinnbild"

    def test_jeder_glyph_gehoert_zu_material_design(self) -> None:
        """Ein Satz, damit die Sinnbilder zueinander passen."""
        fremd = {n: g for n, g in GLYPHS.items() if not g.startswith("mdi6.")}
        assert not fremd, fremd

    def test_ein_unbekannter_name_gibt_ein_leeres_sinnbild(self) -> None:
        """Gegenprobe - ohne sie prueft der Test oben nichts.

        Waere `isNull()` immer False, waeren alle Faelle gruen, auch die
        kaputten.
        """
        assert load_icon("gibt-es-nicht", "#ffffff").isNull()
