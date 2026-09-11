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


class TestEingerastet:
    """Ein eingerasteter Werkzeugknopf muss als Zustand erkennbar sein.

    Bis zum 11.09.2026 trug ihn allein die durchscheinende Flaeche
    `accent_subtle`. Ueber alle 40 Farbschemata und beide Grundpaletten
    gemessen kam die auf 1,16 bis 1,68 gegen ihren Untergrund - weniger,
    als eine blosse Trennlinie erreichen muss. Michael ist es an einem
    dunkelblauen Schema aufgefallen, der Mangel war aber ueberall.
    """

    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_der_eingerastete_knopf_bekommt_einen_rahmen(self, palette: Colors) -> None:
        qss = build_stylesheet(palette)
        block = qss[qss.index("QToolButton:checked") :][:200]
        assert f"border: 1px solid {palette.accent}" in block

    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_der_ruhende_knopf_haelt_den_platz_dafuer_frei(self, palette: Colors) -> None:
        """Sonst springt die Leiste, sobald ein Knopf einrastet."""
        qss = build_stylesheet(palette)
        block = qss[qss.index("QToolButton {") :][:200]
        assert "border: 1px solid transparent" in block

    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_der_rahmen_hebt_sich_von_der_werkzeugleiste_ab(self, palette: Colors) -> None:
        """Die Leiste steht auf bg_secondary, nicht auf dem Fenstergrund."""
        assert contrast_ratio(palette.accent, palette.bg_secondary) >= 2.5

    def test_gedrueckt_und_eingerastet_sind_zwei_dinge(self) -> None:
        """Gedrueckt ist ein Augenblick, eingerastet ein Zustand.

        Stuenden beide in derselben Regel, bekaeme auch der fluechtige
        Druck einen Rahmen - und die Leiste flackerte bei jedem Klick.
        """
        qss = build_stylesheet(DARK)
        gedrueckt = qss[qss.index("QToolButton:pressed") :][:120]
        assert "border:" not in gedrueckt


class TestWerkzeugleiste:
    def test_die_abstaende_stimmen_ueberein(self) -> None:
        qss = build_stylesheet(LIGHT)
        block = qss[qss.index("QToolBar {") :][:200]
        assert "padding: 3px 6px" in block
        assert "spacing: 2px" in block

    def test_die_knoepfe_sind_flach_bis_zum_hover(self) -> None:
        """Flach heisst: nichts zu sehen, nicht: kein Rahmen im Stylesheet.

        Seit dem 11.09.2026 steht dort `1px solid transparent` statt `none` -
        der Platz fuer den Rahmen des eingerasteten Zustands wird freigehalten,
        damit die Leiste beim Einrasten nicht springt. Sichtbar ist davon
        nichts, die Anforderung dieses Tests gilt also unveraendert.
        """
        qss = build_stylesheet(LIGHT)
        block = qss[qss.index("QToolButton {") :][:200]
        assert "background: transparent" in block
        assert "border: 1px solid transparent" in block

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


class TestSchriftAufFarbflaeche:
    """Schrift auf einer Akzentflaeche muss zur Akzentfarbe passen.

    Bis zum 11.09.2026 stand an drei Stellen ein festes Weiss: der
    Auswahlbalken in Tabellen, das Abzeichen im Info-Dialog und die
    nummerierten Punkte im Leerzustand. Das traegt nur, solange der Akzent
    dunkel genug bleibt - Michael hat es an einem Schema mit gelbem Akzent
    gesehen, wo der ausgewaehlte Eintrag unlesbar wurde.

    Auch die Grundpalette war betroffen: weisse Schrift auf dem orangen
    Auswahlbalken kam auf 2,2, schwarze kommt auf 9,4.
    """

    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_die_auswahl_ist_lesbar(self, palette: Colors) -> None:
        from QAppFramework.color import readable_on

        assert contrast_ratio(readable_on(palette.accent), palette.accent) >= 4.5

    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_abzeichen_und_schrittzahlen_ebenso(self, palette: Colors) -> None:
        from QAppFramework.color import readable_on

        qss = build_stylesheet(palette)
        erwartet = readable_on(palette.accent)
        for objekt in ("#AboutBadge", "#StepNumber"):
            block = qss[qss.index(objekt) :][:200]
            assert f"color: {erwartet}" in block, f"{objekt}: {block[:120]}"

    def test_ein_gelber_akzent_bekommt_schwarze_schrift(self) -> None:
        """Der Fall, an dem es aufgefallen ist."""
        from QAppFramework.color import readable_on

        assert readable_on("#FCDD09") == "#000000"

    def test_ein_dunkler_akzent_bekommt_weisse(self) -> None:
        """Gegenprobe - sonst gaebe die Funktion immer dasselbe zurueck."""
        from QAppFramework.color import readable_on

        assert readable_on("#1a1a1a") == "#FFFFFF"


class TestFarbgliederung:
    """Farbe zur Gliederung gibt es nur in den Retro-Schemata.

    Michaels Entscheidung vom 11.09.2026 nach dem Vergleich mit einer TUI:
    die soll farbige Blockrahmen und Spaltenkoepfe bekommen, die
    Grundpalette bleibt das nuechterne Werkzeug, das sie immer war.
    """

    @pytest.mark.parametrize("palette", [LIGHT, DARK], ids=["hell", "dunkel"])
    def test_die_grundpalette_bleibt_zurueckhaltend(self, palette: Colors) -> None:
        assert palette.expressive is False
        qss = build_stylesheet(palette)
        assert "QHeaderView::section" not in qss
        block = qss[qss.index("#EmptyCard") :][:160]
        assert palette.border in block
        assert f"border: 1px solid {palette.accent}" not in block

    def test_ein_retro_schema_gliedert_mit_farbe(self) -> None:
        from QAppFramework.derive import colors_from_palette, palette_for_theme

        marley = palette_for_theme("marley")
        assert marley is not None
        farben = Colors(**colors_from_palette(marley), expressive=True)
        qss = build_stylesheet(farben)
        assert f"QHeaderView::section {{ color: {farben.accent}" in qss
        assert f"#EmptyTitle {{ color: {farben.accent}" in qss

    def test_das_kennzeichen_entscheidet_und_nicht_die_farbe(self) -> None:
        """Gegenprobe: dieselben Farben ohne Kennzeichen ergeben nichts."""
        from QAppFramework.derive import colors_from_palette, palette_for_theme

        marley = palette_for_theme("marley")
        assert marley is not None
        nuechtern = Colors(**colors_from_palette(marley))
        assert "QHeaderView::section" not in build_stylesheet(nuechtern)


class TestFlaechentreppe:
    """Die Flaechen muessen sich voneinander abheben.

    Bis zum 11.09.2026 kamen alle 40 Schemata auf 1,03 bis 1,07 zwischen
    Fenstergrund und Panel - unter jeder Wahrnehmungsschwelle. Sichtbar
    wurde es an einem Dialog, der im Hintergrund verschwand. Die
    Mischanteile stammen aus der Grundpalette, deren Grund schon aufgehellt
    ist; bei fast schwarzem Grund ergeben 2,3 Prozent nichts.
    """

    @pytest.mark.parametrize(
        "name", ["marley", "classic-terminal", "corleone", "cupertino", "plan9"]
    )
    def test_die_flaechen_setzen_sich_ab(self, name: str) -> None:
        from QAppFramework.derive import colors_from_palette, palette_for_theme

        palette = palette_for_theme(name)
        assert palette is not None
        w = colors_from_palette(palette)
        for feld, ziel in (("bg_secondary", 1.03), ("bg_tertiary", 1.05)):
            gemessen = contrast_ratio(w[feld], w["bg_primary"])
            assert gemessen >= ziel, f"{name}.{feld} erreicht nur {gemessen:.3f}"
