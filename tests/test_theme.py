"""Der Look muss mit den uebrigen Qt-Anwendungen uebereinstimmen.

Anforderung: wer von einer Anwendung zur naechsten wechselt, soll sich nicht
umgewoehnen muessen. Die Werte stammen aus jira-timesheet-qt 0.7.1.

Diese Tests halten die Uebereinstimmung fest. Sie pruefen bewusst konkrete
Werte statt "irgendeine Farbe ist gesetzt" - eine Abweichung faellt sonst erst
auf, wenn jemand beide Fenster nebeneinander stellt.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Erscheinungsbild gehoert zur Desktop-Oberflaeche")

from QAppFramework.theme import DARK, LIGHT, TOOLBAR_ICON_SIZE, build_stylesheet  # noqa: E402

# Werte aus jira-timesheet-qt 0.7.1, ui/theme.py. Bei einer Aenderung DORT
# gehoeren sie hier nachgezogen - nicht umgekehrt.
JIRA_TIMESHEET_HELL = {
    "bg_primary": "#f4f5f7",
    "bg_secondary": "#f0f1f4",
    "bg_tertiary": "#ffffff",
    "bg_elevated": "#eceef1",
    "border": "#d3d7dd",
    "text_primary": "#1c1f24",
    "text_secondary": "#5f6773",
    "accent": "#e8590c",
}

JIRA_TIMESHEET_DUNKEL = {
    "bg_primary": "#1f2226",
    "bg_secondary": "#23262b",
    "bg_tertiary": "#26292e",
    "bg_elevated": "#2f333a",
    "border": "#3a3f47",
    "text_primary": "#e2e5ea",
    "text_secondary": "#9aa2ad",
    "accent": "#ff922b",
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
