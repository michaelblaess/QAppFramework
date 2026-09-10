"""Der Look muss mit den uebrigen Qt-Anwendungen uebereinstimmen.

Anforderung: wer von einer Anwendung zur naechsten wechselt, soll sich nicht
umgewoehnen muessen. Die Werte kommen urspruenglich aus jira-timesheet-qt
0.7.1, massgeblich ist inzwischen aber diese Bibliothek - siehe den Kommentar
bei den Konstanten.

Diese Tests halten die Uebereinstimmung fest. Sie pruefen bewusst konkrete
Werte statt "irgendeine Farbe ist gesetzt" - eine Abweichung faellt sonst erst
auf, wenn jemand beide Fenster nebeneinander stellt.

Die Ausnahme davon ist TestKontrast: dort steht die Anforderung statt der
Zahl, weil eine festgenagelte Farbe genau den Fehler nicht faengt, um den es
geht - einen Wert, der seine Rolle nicht mehr erfuellt.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Erscheinungsbild gehoert zur Desktop-Oberflaeche")

from QAppFramework.color import contrast_ratio  # noqa: E402
from QAppFramework.theme import DARK, LIGHT, TOOLBAR_ICON_SIZE, Colors, build_stylesheet  # noqa: E402

# Werte urspruenglich aus jira-timesheet-qt 0.7.1, ui/theme.py.
#
# Die Richtung hat sich seit 0.8.0 umgekehrt: dort ist ui/theme.py nur noch
# eine Bruecke auf diese Bibliothek, und beide Anwendungen beziehen ihre
# Farben von hier. Massgeblich ist also DIESE Datei - eine Aenderung wird
# hier beschlossen und wandert in die Anwendungen, nicht umgekehrt.
#
# `border` steht bewusst nicht mehr in dieser Liste: der Wert ist am
# 10.09.2026 aus Kontrastgruenden angehoben worden und wird jetzt von
# TestKontrast geprueft, das die Anforderung beschreibt statt einer Zahl.
JIRA_TIMESHEET_HELL = {
    "bg_primary": "#f4f5f7",
    "bg_secondary": "#f0f1f4",
    "bg_tertiary": "#ffffff",
    "bg_elevated": "#eceef1",
    "text_primary": "#1c1f24",
    "text_secondary": "#5f6773",
    "accent": "#e8590c",
}

JIRA_TIMESHEET_DUNKEL = {
    "bg_primary": "#1f2226",
    "bg_secondary": "#23262b",
    "bg_tertiary": "#26292e",
    "bg_elevated": "#2f333a",
    "text_primary": "#e2e5ea",
    "text_secondary": "#9aa2ad",
    "accent": "#ff922b",
}

# Die vier Flaechentoene, auf denen Schrift und Linien liegen koennen. Ein
# Kontrast wird gegen JEDEN von ihnen geprueft, nicht nur gegen den
# Fenstergrund: das Stylesheet setzt Trennlinien auch an Werkzeugleiste,
# Statuszeile und Knopfleiste, und dort ist der Untergrund ein anderer.
FLAECHEN = ("bg_primary", "bg_secondary", "bg_tertiary", "bg_elevated")

# Feld und Mindestkontrast. 4.5 ist die WCAG-Schwelle fuer Fliesstext, 3.0
# gilt fuer grosse Schrift und grafische Elemente. Der Hilfstext steht bei
# 12px und faellt streng genommen unter 4.5 - das waere aber ein so dunkler
# Ton, dass er sich vom Fliesstext nicht mehr abhebt und seinen Zweck
# verliert. 1.4 fuer die Linien ist keine WCAG-Zahl, sondern die Schwelle,
# ab der eine Trennlinie auf allen vier Flaechen sichtbar bleibt.
KONTRASTZIELE = {
    "text_primary": 4.5,
    "text_secondary": 4.5,
    "text_tertiary": 3.0,
    "border": 1.4,
    "border_hover": 1.4,
}


class TestPalette:
    @pytest.mark.parametrize(("feld", "wert"), sorted(JIRA_TIMESHEET_HELL.items()))
    def test_helle_palette_stimmt_ueberein(self, feld: str, wert: str) -> None:
        assert getattr(LIGHT, feld) == wert

    @pytest.mark.parametrize(("feld", "wert"), sorted(JIRA_TIMESHEET_DUNKEL.items()))
    def test_dunkle_palette_stimmt_ueberein(self, feld: str, wert: str) -> None:
        assert getattr(DARK, feld) == wert

    def test_der_akzent_ist_orange_nicht_blau(self) -> None:
        """Die Akzentfarbe traegt die Wiedererkennung - sie faerbt den aktiven Reiter."""
        assert LIGHT.accent == "#e8590c"
        assert DARK.accent == "#ff922b"


class TestKontrast:
    """Schrift und Linien muessen auf jeder Flaeche lesbar bleiben.

    Bis zum 10.09.2026 verfehlten in beiden Erscheinungsbildern der
    Hilfstext und die Trennlinie ihr Ziel - aufgefallen ist das erst, als
    jemand gegen alle vier Flaechentoene gemessen hat statt nur gegen den
    Fenstergrund. Diese Tests halten die Korrektur fest und beschreiben die
    Anforderung, nicht die Zahl: wer einen Farbwert aendert, sieht sofort,
    ob er unter die Schwelle rutscht.
    """

    @pytest.mark.parametrize(("feld", "ziel"), sorted(KONTRASTZIELE.items()))
    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_jede_rolle_traegt_auf_jeder_flaeche(self, palette: Colors, feld: str, ziel: float) -> None:
        vorne = getattr(palette, feld)
        schwaechster = min(contrast_ratio(vorne, getattr(palette, f)) for f in FLAECHEN)
        assert schwaechster >= ziel, (
            f"{feld} ({vorne}) erreicht nur {schwaechster:.2f} statt {ziel} auf der schwaechsten der vier Flaechen"
        )

    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_der_hover_zustand_hebt_sich_von_der_ruhenden_linie_ab(self, palette: Colors) -> None:
        """Sonst zeigt die Oberflaeche nicht mehr an, wo der Mauszeiger steht.

        Die Schwelle ist niedrig angesetzt: 1.1 findet einen zugelaufenen
        Wert, ohne eine kuenftige Feinabstimmung der Toene zu verbieten.
        """
        assert contrast_ratio(palette.border, palette.border_hover) >= 1.1

    def test_die_messung_kann_scheitern(self) -> None:
        """Gegenprobe - ohne sie belegt ein gruener Lauf oben nichts.

        Eine Farbe, die der Flaeche gleicht, muss durchfallen.
        """
        assert contrast_ratio(LIGHT.bg_primary, LIGHT.bg_primary) < 1.4
        assert contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0, abs=0.1)


class TestReiter:
    def test_der_aktive_reiter_traegt_die_akzentfarbe(self) -> None:
        qss = build_stylesheet(LIGHT)
        assert "#ViewTabs::tab:selected" in qss
        assert f"color: {LIGHT.accent}" in qss

    def test_der_aktive_reiter_ist_fett_und_unterstrichen(self) -> None:
        qss = build_stylesheet(LIGHT)
        block = qss[qss.index("#ViewTabs::tab:selected") :][:200]
        assert "font-weight: 700" in block
        assert f"border-bottom: 2px solid {LIGHT.accent}" in block

    def test_die_reiterleiste_heisst_viewtabs(self) -> None:
        """Derselbe Objektname wie dort - sonst greifen die Regeln nicht."""
        assert "#ViewTabs {" in build_stylesheet(LIGHT)


class TestWerkzeugleiste:
    def test_die_abstaende_stimmen_ueberein(self) -> None:
        qss = build_stylesheet(LIGHT)
        block = qss[qss.index("QToolBar {") :][:200]
        assert "padding: 3px 6px" in block
        assert "spacing: 2px" in block

    def test_die_knoepfe_sind_flach_bis_zum_hover(self) -> None:
        qss = build_stylesheet(LIGHT)
        block = qss[qss.index("QToolButton {") :][:200]
        assert "background: transparent" in block
        assert "border: none" in block

    def test_die_bibliothek_setzt_keine_sinnbildgroesse_vor(self) -> None:
        """Qt liefert 24 Pixel fuer Werkzeugleisten - Anwendungen sollen nichts setzen.

        Der Wert steht hier nur als Erwartung. Wer ihn in einer Anwendung
        ueberschreibt, bekommt Leisten, die unterschiedlich aussehen.
        """
        from PySide6.QtWidgets import QApplication, QMainWindow

        app = QApplication.instance() or QApplication([])
        assert app is not None
        fenster = QMainWindow()
        assert fenster.addToolBar("probe").iconSize().width() == TOOLBAR_ICON_SIZE
        fenster.close()
