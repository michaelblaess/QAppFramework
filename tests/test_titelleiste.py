"""Die Fenstertitelleiste folgt dem Theme - unter Windows.

Sie zeichnet das Betriebssystem, nicht Qt. Bei einem dunklen Theme stand
deshalb ein helles Windows-Band ueber einer dunklen Oberflaeche.

Das Ergebnis laesst sich nicht knipsen: die Titelleiste steckt nicht im
Fensterabbild, das `QWidget.grab()` liefert. Geprueft wird deshalb, dass
die Aufrufe durchgehen und dass die Farbumrechnung stimmt - beim Rest
haengt es an Windows.
"""

from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Fenster gehoeren zur Desktop-Oberflaeche")

from PySide6.QtWidgets import QApplication, QDialog, QLabel  # noqa: E402

from QAppFramework.theme import DARK, LIGHT  # noqa: E402
from QAppFramework.titlebar import (  # noqa: E402
    _colorref,
    border_color,
    style_all_windows,
    style_window,
    watch_new_windows,
)


@pytest.fixture(scope="module")
def anwendung() -> QApplication:
    vorhanden = QApplication.instance()
    return vorhanden if isinstance(vorhanden, QApplication) else QApplication([])


class TestFarbumrechnung:
    """COLORREF ist 0x00BBGGRR - umgekehrt zu HTML.

    Wer das uebersieht, bekommt eine Titelleiste in der Komplementaerfarbe
    und sucht den Fehler lange im Theme.
    """

    def test_die_kanaele_stehen_umgekehrt(self) -> None:
        # Reines Rot: in HTML 0xFF0000, als COLORREF 0x0000FF.
        assert _colorref("#FF0000") == 0x0000FF
        assert _colorref("#0000FF") == 0xFF0000

    def test_gruen_bleibt_in_der_mitte(self) -> None:
        assert _colorref("#00FF00") == 0x00FF00

    def test_eine_echte_themefarbe(self) -> None:
        assert _colorref("#1F4433") == 0x33441F


class TestEinfaerben:
    def test_ein_fenster_laesst_sich_einfaerben(self, anwendung: QApplication) -> None:
        """Unter Windows. Anderswo meldet die Funktion sauber False."""
        dialog = QDialog()
        dialog.show()
        anwendung.processEvents()
        try:
            ergebnis = style_window(dialog, DARK)
            if sys.platform == "win32":
                assert ergebnis is True
            else:
                assert ergebnis is False
        finally:
            dialog.close()

    def test_ein_widget_ohne_eigenes_fenster_wird_uebergangen(
        self, anwendung: QApplication
    ) -> None:
        """Eine Beschriftung im Dialog hat keine Titelleiste."""
        dialog = QDialog()
        beschriftung = QLabel("kein Fenster", dialog)
        dialog.show()
        anwendung.processEvents()
        try:
            assert style_window(beschriftung, DARK) is False
        finally:
            dialog.close()

    def test_beide_paletten_gehen_durch(self, anwendung: QApplication) -> None:
        """Hell setzt den Dunkelmodus aus, dunkel ein - beides darf nicht werfen."""
        dialog = QDialog()
        dialog.show()
        anwendung.processEvents()
        try:
            for palette in (LIGHT, DARK):
                style_window(dialog, palette)
        finally:
            dialog.close()

    def test_alle_fenster_auf_einmal(self, anwendung: QApplication) -> None:
        dialog = QDialog()
        dialog.show()
        anwendung.processEvents()
        try:
            gezaehlt = style_all_windows(DARK)
            if sys.platform == "win32":
                assert gezaehlt >= 1
            else:
                assert gezaehlt == 0
        finally:
            dialog.close()


class TestFensterwache:
    def test_die_wache_laesst_sich_mehrfach_setzen(self, anwendung: QApplication) -> None:
        """Sonst haengen nach jedem Themewechsel weitere Filter an der Anwendung."""
        from QAppFramework import titlebar

        watch_new_windows()
        erste = titlebar._wache
        watch_new_windows()
        assert titlebar._wache is erste


class TestRahmenton:
    """Der Fensterrahmen: ruhig am Hauptfenster, im Akzent am Dialog.

    Michael am 11.09.2026 zu Jokers Giftgruen: "der Rahmen ist heftig" - um
    ein Vollfenster wird ein Akzentrahmen zum Leuchtband. Am 14.09.2026 zum
    Einstellungsdialog: "Der Rahmen ist nicht einheitlich". Das Stylesheet
    zog dort eine eigene Linie, die nur den Inhalt umlief und unter der
    Titelleiste endete - gemessen am echten Fenster.
    """

    def test_das_hauptfenster_bleibt_ruhig(self, anwendung: QApplication) -> None:
        from dataclasses import replace

        from PySide6.QtWidgets import QMainWindow

        laut = replace(DARK, expressive=True)
        fenster = QMainWindow()
        assert border_color(fenster, laut) == laut.border

    def test_ein_dialog_nimmt_bei_ausdrucksstarken_themes_den_akzent(self, anwendung: QApplication) -> None:
        from dataclasses import replace

        laut = replace(DARK, expressive=True)
        dialog = QDialog()
        assert border_color(dialog, laut) == laut.accent
        assert border_color(dialog, DARK) == DARK.border, "Die Grundpalette bleibt nuechtern"

    def test_style_window_reicht_die_rahmenfarbe_durch(self) -> None:
        """Gelesen am Quelltext: was Windows aus dem Rahmen macht, steckt in keinem Fensterabbild."""
        from pathlib import Path

        import QAppFramework.titlebar as modul

        quelltext = Path(modul.__file__).read_text(encoding="utf-8")
        zeile = next(z for z in quelltext.splitlines() if "DWMWA_BORDER_COLOR" in z and "setze(" in z)
        assert "border_color(widget, p)" in zeile

    def test_das_stylesheet_zieht_keine_eigene_dialoglinie(self) -> None:
        from dataclasses import replace

        from QAppFramework.theme import build_stylesheet

        assert "QDialog {" not in build_stylesheet(replace(DARK, expressive=True))
