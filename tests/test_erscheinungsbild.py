"""Erscheinungsbild, Akzentfarbe und Zoom zur Laufzeit.

Bis 0.2.0 las die Bibliothek einmal das Farbschema des Systems und war danach
festgelegt. Ein Umschalter oder eine Darstellungs-Seite in den Einstellungen
liess sich darauf nicht bauen.

Geprueft wird deshalb die Wirkung: aendert sich nach dem Umstellen wirklich,
was die Anwendung zu sehen bekommt - Farbwerte, Stylesheet, Palette.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Erscheinungsbild gehoert zur Desktop-Oberflaeche")

from PySide6.QtGui import QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from QAppFramework import theme  # noqa: E402
from QAppFramework.theme import (  # noqa: E402
    AKZENTE,
    DUNKEL,
    HELL,
    STANDARD_AKZENT,
    STANDARD_ZOOM,
    ZOOMSTUFEN,
    Modus,
    akzent,
    akzent_namen,
    anwenden,
    baue_qss,
    farben,
    ist_dunkel,
    modus,
    naechster_zoom,
    setze_akzent,
    setze_modus,
    setze_zoom,
    umgeschaltet,
    zoom,
)


@pytest.fixture(autouse=True)
def _zustand_zuruecksetzen() -> Iterator[None]:
    """Modus, Akzent und Zoom sind Modulzustand.

    Ohne Zuruecksetzen faerbt ein Test den naechsten, und welcher gewinnt,
    haengt an der Reihenfolge.
    """
    yield
    setze_modus(Modus.SYSTEM)
    setze_akzent(STANDARD_AKZENT)
    setze_zoom(STANDARD_ZOOM)


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    return vorhanden if isinstance(vorhanden, QApplication) else QApplication([])


class TestErscheinungsbild:
    def test_dunkel_und_hell_liefern_verschiedene_flaechen(self) -> None:
        setze_modus(Modus.DUNKEL)
        dunkel = farben()
        setze_modus(Modus.HELL)
        hell = farben()
        assert dunkel.bg_primary == DUNKEL.bg_primary
        assert hell.bg_primary == HELL.bg_primary
        assert dunkel.bg_primary != hell.bg_primary

    def test_der_modus_schlaegt_das_betriebssystem(self) -> None:
        """Genau das ging bis 0.2.0 nicht - ist_dunkel fragte immer das System."""
        setze_modus(Modus.HELL)
        assert ist_dunkel() is False
        setze_modus(Modus.DUNKEL)
        assert ist_dunkel() is True

    def test_bei_system_entscheidet_das_betriebssystem(self, monkeypatch: pytest.MonkeyPatch) -> None:
        setze_modus(Modus.SYSTEM)
        monkeypatch.setattr(theme, "system_ist_dunkel", lambda: True)
        assert ist_dunkel() is True
        monkeypatch.setattr(theme, "system_ist_dunkel", lambda: False)
        assert ist_dunkel() is False

    def test_ein_unbekannter_modus_faellt_auf_system_zurueck(self) -> None:
        """Eine Einstellungsdatei von einem neueren Stand darf nichts umwerfen."""
        setze_modus("gibtesnicht")
        assert modus() is Modus.SYSTEM

    def test_umgeschaltet_liefert_das_gegenteil_des_sichtbaren(self) -> None:
        setze_modus(Modus.DUNKEL)
        assert umgeschaltet() is Modus.HELL
        setze_modus(Modus.HELL)
        assert umgeschaltet() is Modus.DUNKEL

    def test_umgeschaltet_wirkt_auch_aus_system_heraus(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sonst waere der erste Druck wirkungslos, wenn das System schon dunkel ist."""
        setze_modus(Modus.SYSTEM)
        monkeypatch.setattr(theme, "system_ist_dunkel", lambda: True)
        assert umgeschaltet() is Modus.HELL


class TestAkzentfarbe:
    def test_der_akzent_landet_in_den_farben(self) -> None:
        setze_modus(Modus.DUNKEL)
        setze_akzent("blau")
        assert farben().accent == AKZENTE["blau"][0].accent
        assert farben().accent != DUNKEL.accent

    def test_hell_und_dunkel_haben_eigene_toene(self) -> None:
        """Ein Ton, der auf dunklem Grund traegt, wird auf hellem zu blass."""
        setze_akzent("blau")
        setze_modus(Modus.DUNKEL)
        auf_dunkel = farben().accent
        setze_modus(Modus.HELL)
        assert farben().accent != auf_dunkel

    def test_der_akzent_faerbt_den_aktiven_reiter(self) -> None:
        """Die Akzentfarbe traegt die Wiedererkennung - sie muss im Stylesheet ankommen."""
        setze_modus(Modus.DUNKEL)
        setze_akzent("violett")
        block = baue_qss(farben())
        stelle = block.index("#ViewTabs::tab:selected")
        assert AKZENTE["violett"][0].accent in block[stelle : stelle + 200]

    def test_ein_unbekannter_akzent_faellt_auf_den_standard_zurueck(self) -> None:
        setze_akzent("neonpink")
        assert akzent() == STANDARD_AKZENT

    def test_jede_akzentfarbe_hat_einen_anzeigenamen(self) -> None:
        for sprache in ("de", "en"):
            namen = akzent_namen(sprache)
            assert set(namen) == set(AKZENTE)
            assert all(wert and wert != schluessel for schluessel, wert in namen.items())


class TestZoom:
    def test_der_zoom_vergroessert_die_schrift_im_stylesheet(self) -> None:
        setze_zoom(STANDARD_ZOOM)
        normal = self._groessen(baue_qss(farben()))
        setze_zoom(150)
        gross = self._groessen(baue_qss(farben()))
        assert normal, "Im Stylesheet steht keine einzige Schriftgroesse"
        assert len(gross) == len(normal)
        assert all(g > n for g, n in zip(gross, normal, strict=True))

    def test_hundert_prozent_laesst_das_stylesheet_unveraendert(self) -> None:
        setze_zoom(STANDARD_ZOOM)
        assert self._groessen(baue_qss(farben())) == self._groessen(baue_qss(farben()))

    def test_der_zoom_bleibt_zwischen_den_stufen(self) -> None:
        setze_zoom(5)
        assert zoom() == ZOOMSTUFEN[0]
        setze_zoom(9000)
        assert zoom() == ZOOMSTUFEN[-1]

    def test_die_naechste_stufe_verlaesst_die_enden_nicht(self) -> None:
        setze_zoom(ZOOMSTUFEN[-1])
        assert naechster_zoom(1) == ZOOMSTUFEN[-1]
        setze_zoom(ZOOMSTUFEN[0])
        assert naechster_zoom(-1) == ZOOMSTUFEN[0]
        setze_zoom(STANDARD_ZOOM)
        assert naechster_zoom(1) > STANDARD_ZOOM

    @staticmethod
    def _groessen(qss: str) -> list[int]:
        return [int(wert) for wert in re.findall(r"font-size:\s*(\d+)px", qss)]


class TestAnwenden:
    def test_ein_wechsel_faerbt_die_anwendung_um(self, app: QApplication) -> None:
        """Der Beweis am Ende der Kette: die Palette der Anwendung selbst."""
        setze_modus(Modus.HELL)
        anwenden(app)
        hell = app.palette().color(QPalette.ColorRole.Window).name()

        setze_modus(Modus.DUNKEL)
        anwenden(app)
        dunkel = app.palette().color(QPalette.ColorRole.Window).name()

        assert hell != dunkel
        assert dunkel == DUNKEL.bg_primary
        assert hell == HELL.bg_primary

    def test_der_akzent_landet_in_der_auswahlfarbe(self, app: QApplication) -> None:
        setze_modus(Modus.DUNKEL)
        setze_akzent("gruen")
        anwenden(app)
        markiert = app.palette().color(QPalette.ColorRole.Highlight).name()
        assert markiert == AKZENTE["gruen"][0].accent

    def test_dunkel_als_argument_uebersteuert_die_einstellung(self, app: QApplication) -> None:
        """Fuer Vorschauen und Tests, ohne die Einstellung anzufassen."""
        setze_modus(Modus.DUNKEL)
        assert anwenden(app, dunkel=False).bg_primary == HELL.bg_primary
        assert modus() is Modus.DUNKEL


class TestUmschalten:
    def test_umschalten_wechselt_und_wendet_an(self, app: QApplication) -> None:
        """Der Umschalter der Werkzeugleiste - ein Aufruf, sichtbares Ergebnis."""
        from QAppFramework.theme import umschalten

        setze_modus(Modus.HELL)
        anwenden(app)
        vorher = app.palette().color(QPalette.ColorRole.Window).name()

        neuer = umschalten(app)

        assert neuer is Modus.DUNKEL
        assert modus() is Modus.DUNKEL
        assert app.palette().color(QPalette.ColorRole.Window).name() != vorher

    def test_zweimal_umschalten_ist_wieder_am_anfang(self, app: QApplication) -> None:
        from QAppFramework.theme import umschalten

        setze_modus(Modus.DUNKEL)
        umschalten(app)
        assert umschalten(app) is Modus.DUNKEL


class TestEigenesStylesheet:
    def test_eigene_regeln_lassen_sich_mitskalieren(self) -> None:
        """Eine Anwendung haengt eigene Regeln an - die muessen mitwachsen.

        Ohne das bleiben genau die auf fester Groesse, waehrend der Rest der
        Oberflaeche zoomt. Aufgefallen beim Umbau von jira-timesheet-qt.
        """
        from QAppFramework.theme import skaliere

        setze_zoom(200)
        assert skaliere("#Eigen { font-size: 13px; }") == "#Eigen { font-size: 26px; }"

    def test_ohne_zoom_bleibt_der_text_wie_er_ist(self) -> None:
        from QAppFramework.theme import skaliere

        setze_zoom(STANDARD_ZOOM)
        eigen = "#Eigen { font-size: 13px; }"
        assert skaliere(eigen) == eigen
