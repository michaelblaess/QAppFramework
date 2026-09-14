"""Einstellungsdialog.

Geprueft wird an einer echten Unterklasse, nicht an der Basis allein: das
Zusammenspiel ist der Punkt - die Anwendung liefert Seiten und liest ihre
Felder aus, die Bibliothek liefert Geruest, Appearance und Speicherort.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Der Einstellungsdialog gehoert zur Desktop-Oberflaeche")

from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QWidget,
)

from QAppFramework.settings import (  # noqa: E402
    Appearance,
    SettingsDialogBase,
)
from QAppFramework.theme import Mode, apply_theme  # noqa: E402


class ProbeDialog(SettingsDialogBase):
    """Eine Anwendung mit einer eigenen Seite und einem Speicherort."""

    def __init__(self, darstellung: Appearance, orte: Sequence[tuple[str, Path]] = (), **rest: object) -> None:
        # VOR super().__init__ - der Konstruktor der Basis ruft eigene_seiten().
        self.gelesen = ""
        self._orte = tuple(orte)
        super().__init__(darstellung, **rest)  # type: ignore[arg-type]

    def eigene_seiten(self) -> Sequence[tuple[str, QWidget]]:
        seite, formular = self.seite("Zugang")
        self._feld = QLineEdit("start")
        formular.addRow(self.beschriftung("Adresse"), self._feld)
        formular.addRow(self.hinweis("Ein erklaerender Satz."))
        self._farbe = self.farbknopf("#ff0000", "Markierung")
        formular.addRow(self.beschriftung("Farbe"), self._farbe)
        return [("Zugang", seite)]

    def uebernehmen(self) -> None:
        self.gelesen = self._feld.text()

    def speicherorte(self) -> Sequence[tuple[str, Path]]:
        return self._orte


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    fertig = vorhanden if isinstance(vorhanden, QApplication) else QApplication([])
    apply_theme(fertig, dunkel=False)
    return fertig


@pytest.fixture
def dialog(app: QApplication, tmp_path: Path) -> Iterator[ProbeDialog]:
    d = ProbeDialog(
        Appearance(mode=Mode.LIGHT, accent="blau", zoom=110),
        orte=[("Einstellungen", tmp_path / "einstellungen.json")],
    )
    d.show()
    app.processEvents()
    yield d
    d.close()


class TestGeruest:
    def test_die_eigene_seite_steht_vor_denen_der_bibliothek(self, dialog: ProbeDialog) -> None:
        """Appearance und Speicherort gehoeren ans Ende - dort sucht sie jeder."""
        nav = dialog.findChild(QListWidget, "SettingsNav")
        assert nav is not None
        beschriftungen = [nav.item(i).text() for i in range(nav.count())]
        assert beschriftungen == ["Zugang", "Darstellung", "Speicherort"]

    def test_die_erste_seite_ist_vorgewaehlt(self, dialog: ProbeDialog) -> None:
        nav = dialog.findChild(QListWidget, "SettingsNav")
        assert nav is not None
        assert nav.currentRow() == 0

    def test_ohne_speicherorte_bleibt_die_seite_weg(self, app: QApplication) -> None:
        d = ProbeDialog(Appearance())
        nav = d.findChild(QListWidget, "SettingsNav")
        assert nav is not None
        assert [nav.item(i).text() for i in range(nav.count())] == ["Zugang", "Darstellung"]
        d.close()

    def test_jede_seite_liegt_in_einem_bildlaufbereich(self, dialog: ProbeDialog) -> None:
        """Ohne den ist eine zu hohe Seite nicht abgeschnitten, sondern unerreichbar."""
        bereiche = dialog.findChildren(QScrollArea, "SettingsScroll")
        assert len(bereiche) == 3
        assert all(b.widgetResizable() for b in bereiche)

    def test_der_dialog_hat_einen_groessengriff(self, dialog: ProbeDialog) -> None:
        assert dialog.isSizeGripEnabled()

    def test_abbrechen_steht_zuletzt(self, dialog: ProbeDialog) -> None:
        """Wie in jedem Windows-Dialog. Bis zum 14.09.2026 stand es links von Speichern."""
        speichern = dialog.findChild(QPushButton, "SettingsSave")
        abbrechen = dialog.findChild(QPushButton, "SettingsCancel")
        assert speichern is not None
        assert abbrechen is not None
        links = speichern.mapTo(dialog, speichern.rect().topLeft()).x()
        rechts = abbrechen.mapTo(dialog, abbrechen.rect().topLeft()).x()
        assert links < rechts, f"Speichern bei x={links}, Abbrechen bei x={rechts}"


class TestDarstellung:
    def test_die_uebergebenen_werte_stehen_in_den_feldern(self, dialog: ProbeDialog) -> None:
        assert dialog._feld_modus.currentData() == Mode.LIGHT.value
        assert dialog._feld_akzent.currentData() == "blau"
        assert dialog._feld_zoom.currentData() == 110

    def test_speichern_gibt_die_geaenderte_darstellung_zurueck(self, dialog: ProbeDialog) -> None:
        dialog._feld_modus.setCurrentIndex(dialog._feld_modus.findData(Mode.DARK.value))
        dialog._feld_akzent.setCurrentIndex(dialog._feld_akzent.findData("gruen"))
        dialog._feld_zoom.setCurrentIndex(dialog._feld_zoom.findData(125))
        dialog._speichern()
        assert dialog.darstellung == Appearance(mode=Mode.DARK, accent="gruen", zoom=125)

    def test_abbrechen_laesst_die_darstellung_stehen(self, dialog: ProbeDialog) -> None:
        vorher = dialog.darstellung
        dialog._feld_akzent.setCurrentIndex(dialog._feld_akzent.findData("violett"))
        dialog.reject()
        assert dialog.darstellung == vorher

    def test_die_auswahl_zeigt_alle_akzentfarben(self, dialog: ProbeDialog) -> None:
        from QAppFramework.theme import ACCENTS

        werte = {dialog._feld_akzent.itemData(i) for i in range(dialog._feld_akzent.count())}
        assert werte == set(ACCENTS)

    def test_die_auswahl_passt_sich_langen_eintraegen_an(self, dialog: ProbeDialog) -> None:
        """Ohne AdjustToContents bleibt sie auf der Breite des ersten Anzeigens stehen."""
        from PySide6.QtWidgets import QComboBox

        assert dialog._feld_modus.sizeAdjustPolicy() == QComboBox.SizeAdjustPolicy.AdjustToContents


class TestEigeneSeite:
    def test_speichern_ruft_uebernehmen(self, dialog: ProbeDialog) -> None:
        dialog._feld.setText("geaendert")
        dialog._speichern()
        assert dialog.gelesen == "geaendert"

    def test_abbrechen_ruft_uebernehmen_nicht(self, dialog: ProbeDialog) -> None:
        dialog._feld.setText("geaendert")
        dialog.reject()
        assert dialog.gelesen == ""

    def test_der_farbknopf_haelt_seinen_wert(self, dialog: ProbeDialog) -> None:
        assert dialog.farbe_von(dialog._farbe) == "FF0000"
        assert dialog._farbe.text() == "#FF0000"

    def test_der_farbknopf_waehlt_lesbare_schrift(self, app: QApplication) -> None:
        """Auf dunklem Grund weiss, auf hellem schwarz - sonst liest es niemand."""
        d = ProbeDialog(Appearance())
        for wert, erwartet in (("FFFF00", "#000000"), ("101010", "#ffffff")):
            knopf = d.farbknopf(wert)
            assert erwartet in knopf.styleSheet()
        d.close()


class TestSpeicherort:
    def test_der_pfad_steht_im_dialog(self, dialog: ProbeDialog, tmp_path: Path) -> None:
        pfade = [w.text() for w in dialog.findChildren(QLabel, "SettingsPath")]
        assert str(tmp_path / "einstellungen.json") in pfade

    def test_jeder_pfad_hat_einen_oeffnen_knopf(self, dialog: ProbeDialog) -> None:
        knoepfe = [k for k in dialog.findChildren(QPushButton) if k.text() == "Öffnen"]
        assert len(knoepfe) == 1

    def test_oeffnen_legt_ein_fehlendes_verzeichnis_an(self, tmp_path: Path) -> None:
        """Sonst tut der Klick beim ersten Start nichts, und niemand weiss warum."""
        ziel = tmp_path / "neu" / "datei.json"
        assert not ziel.parent.exists()
        SettingsDialogBase.oeffne(ziel)
        assert ziel.parent.is_dir()


class TestSprache:
    def test_englisch_uebersetzt_geruest_und_seiten(self, app: QApplication) -> None:
        d = ProbeDialog(Appearance(), sprache="en")
        nav = d.findChild(QListWidget, "SettingsNav")
        assert nav is not None
        assert [nav.item(i).text() for i in range(nav.count())] == ["Zugang", "Appearance"]
        assert {k.text() for k in d.findChildren(QPushButton)} >= {"Save", "Cancel"}
        assert d.windowTitle() == "Settings"
        d.close()


class TestErweiterteDarstellung:
    """Eigene Zeilen auf der Darstellungs-Seite.

    Fuer Markierungsfarben und Ampelschwellen: sie gehoeren fuer den Anwender
    zur Appearance, auch wenn nur eine Anwendung sie kennt.
    """

    def test_eigene_zeilen_stehen_auf_der_seite(self, app: QApplication) -> None:
        from PySide6.QtWidgets import QCheckBox, QFormLayout

        class MitErweiterung(ProbeDialog):
            def darstellung_erweitern(self, formular: QFormLayout) -> None:
                self.haken = QCheckBox("Manuelle Zeiten hervorheben")
                formular.addRow(self.beschriftung(""), self.haken)

        d = MitErweiterung(Appearance())
        d.show()
        app.processEvents()
        # Ueber findChildren: das Widget muss wirklich im Dialog haengen,
        # nicht nur als Feld existieren. Der Schalter der Bibliothek ist
        # ebenfalls ein Kontrollkaestchen und faellt ueber seinen
        # Objektnamen heraus.
        eigene = [h for h in d.findChildren(QCheckBox) if h.objectName() != "SettingsThemesToggle"]
        assert eigene == [d.haken]
        # Und zwar auf der Darstellungs-Seite, nicht irgendwo.
        nav = d.findChild(QListWidget, "SettingsNav")
        assert nav is not None
        nav.setCurrentRow([nav.item(i).text() for i in range(nav.count())].index("Darstellung"))
        app.processEvents()
        assert d.haken.isVisible(), "Die eigene Zeile steht nicht auf der Darstellungs-Seite"
        d.close()

    def test_ohne_erweiterung_bleibt_die_seite_wie_sie_ist(self, dialog: ProbeDialog) -> None:
        """Nur der Schalter der Bibliothek, sonst kein Kontrollkaestchen."""
        from PySide6.QtWidgets import QCheckBox

        namen = [h.objectName() for h in dialog.findChildren(QCheckBox)]
        assert namen == ["SettingsThemesToggle"]


class TestThemeSchalter:
    """Themes sind ein eigener Modus, kein Eintrag zwischen anderen.

    Michaels Entscheidung vom 11.09.2026: wer mit Themes nichts anfangen
    kann, soll in den Einstellungen gar nicht erst darueber stolpern -
    Erscheinungsbild und Akzentfarbe bleiben, wie sie immer waren. Wer sie
    einschaltet, bekommt die Themeliste, und die beiden anderen Felder
    verschwinden, weil sie dann ohnehin nicht mehr gelten.
    """

    def test_ohne_schalter_gilt_die_grundpalette(self) -> None:
        from QAppFramework import colors, set_theme, set_themes_enabled
        from QAppFramework.theme import LIGHT, Mode, set_mode

        set_mode(Mode.LIGHT)
        set_theme("marley")
        set_themes_enabled(False)
        try:
            assert colors().bg_primary == LIGHT.bg_primary
        finally:
            set_theme("")
            set_mode(Mode.SYSTEM)

    def test_der_name_ueberlebt_das_abschalten(self) -> None:
        """Sonst muesste man beim Wiedereinschalten von vorn suchen."""
        from QAppFramework import current_theme, set_theme, set_themes_enabled

        set_theme("marley")
        set_themes_enabled(True)
        set_themes_enabled(False)
        try:
            assert current_theme() == "marley"
        finally:
            set_theme("")
            set_themes_enabled(False)

    def test_eingeschaltet_bestimmt_das_theme_die_farben(self) -> None:
        from QAppFramework import colors, set_theme, set_themes_enabled
        from QAppFramework.derive import colors_from_palette, palette_for_theme

        marley = palette_for_theme("marley")
        assert marley is not None
        set_theme("marley")
        set_themes_enabled(True)
        try:
            assert colors().bg_primary == colors_from_palette(marley)["bg_primary"]
        finally:
            set_theme("")
            set_themes_enabled(False)

    def test_der_vorschlag_passt_zum_erscheinungsbild(self) -> None:
        """Wer einschaltet, soll nicht auf einer unveraenderten Flaeche raten."""
        from QAppFramework import default_theme
        from QAppFramework.derive import palette_for_theme

        for dunkel in (True, False):
            palette = palette_for_theme(default_theme(dunkel))
            assert palette is not None
            assert palette.dark is dunkel, f"Vorschlag fuer dunkel={dunkel} passt nicht"


class TestFelderWechseln:
    """Der Schalter blendet um, statt wirkungslose Felder stehenzulassen.

    Das war der Anlass: Erscheinungsbild, Akzentfarbe und Theme standen
    nebeneinander, und zwei davon galten nicht mehr, sobald das dritte
    gesetzt war. Ein Hinweistext musste es erklaeren.

    Geprueft wird mit `isHidden()` und nicht mit `isVisible()`: letzteres
    ist false, solange die Darstellungs-Seite nicht die aufgeschlagene ist,
    und das hat mit dem Schalter nichts zu tun.
    """

    @staticmethod
    def _sichtbar(dialog: ProbeDialog) -> tuple[bool, bool, bool]:
        """Modus, Akzent, Theme - was davon steht."""
        return (
            not dialog._feld_modus.isHidden(),
            not dialog._feld_akzent.isHidden(),
            not dialog._feld_theme.isHidden(),
        )

    def test_ohne_themes_stehen_erscheinungsbild_und_akzent(self, app: QApplication) -> None:
        d = ProbeDialog(Appearance(themes_enabled=False))
        d.show()
        app.processEvents()
        try:
            assert self._sichtbar(d) == (True, True, False)
        finally:
            d.close()

    def test_mit_themes_steht_die_themeliste(self, app: QApplication) -> None:
        d = ProbeDialog(Appearance(themes_enabled=True, theme="marley"))
        d.show()
        app.processEvents()
        try:
            assert self._sichtbar(d) == (False, False, True)
        finally:
            d.close()

    def test_der_schalter_wirkt_sofort(self, app: QApplication) -> None:
        """Ohne Neuaufbau des Dialogs - sonst waere er unbrauchbar."""
        d = ProbeDialog(Appearance(themes_enabled=False))
        d.show()
        app.processEvents()
        try:
            assert self._sichtbar(d) == (True, True, False)
            d._feld_themes_an.setChecked(True)
            app.processEvents()
            assert self._sichtbar(d) == (False, False, True)
            d._feld_themes_an.setChecked(False)
            app.processEvents()
            assert self._sichtbar(d) == (True, True, False)
        finally:
            d.close()

    def test_beim_einschalten_wird_ein_theme_vorgeschlagen(self, app: QApplication) -> None:
        d = ProbeDialog(Appearance(themes_enabled=False, theme=""))
        d.show()
        app.processEvents()
        try:
            d._feld_themes_an.setChecked(True)
            app.processEvents()
            assert d._feld_theme.currentData(), "Kein Theme vorgeschlagen"
        finally:
            d.close()

    def test_ein_gemerktes_theme_wird_nicht_ueberschrieben(self, app: QApplication) -> None:
        """Wer wieder einschaltet, macht dort weiter, wo er war."""
        d = ProbeDialog(Appearance(themes_enabled=False, theme="beastie"))
        d.show()
        app.processEvents()
        try:
            d._feld_themes_an.setChecked(True)
            app.processEvents()
            assert d._feld_theme.currentData() == "beastie"
        finally:
            d.close()

    def test_der_schalter_landet_im_ergebnis(self, app: QApplication) -> None:
        d = ProbeDialog(Appearance(themes_enabled=False))
        d.show()
        app.processEvents()
        try:
            d._feld_themes_an.setChecked(True)
            d._speichern()
            assert d.darstellung.themes_enabled is True
        finally:
            d.close()
