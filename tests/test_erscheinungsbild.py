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
    ACCENTS,
    DARK,
    DEFAULT_ACCENT,
    DEFAULT_ZOOM,
    LIGHT,
    ZOOM_LEVELS,
    Mode,
    accent,
    accent_names,
    apply_theme,
    build_stylesheet,
    colors,
    is_dark,
    mode,
    next_zoom,
    set_accent,
    set_mode,
    set_zoom,
    toggled,
    zoom,
)


@pytest.fixture(autouse=True)
def _zustand_zuruecksetzen() -> Iterator[None]:
    """Mode, Accent und Zoom sind Modulzustand.

    Ohne Zuruecksetzen faerbt ein Test den naechsten, und welcher gewinnt,
    haengt an der Reihenfolge.
    """
    yield
    set_mode(Mode.SYSTEM)
    set_accent(DEFAULT_ACCENT)
    set_zoom(DEFAULT_ZOOM)


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    return vorhanden if isinstance(vorhanden, QApplication) else QApplication([])


class TestErscheinungsbild:
    def test_dunkel_und_hell_liefern_verschiedene_flaechen(self) -> None:
        set_mode(Mode.DARK)
        dunkel = colors()
        set_mode(Mode.LIGHT)
        hell = colors()
        assert dunkel.bg_primary == DARK.bg_primary
        assert hell.bg_primary == LIGHT.bg_primary
        assert dunkel.bg_primary != hell.bg_primary

    def test_der_modus_schlaegt_das_betriebssystem(self) -> None:
        """Genau das ging bis 0.2.0 nicht - is_dark fragte immer das System."""
        set_mode(Mode.LIGHT)
        assert is_dark() is False
        set_mode(Mode.DARK)
        assert is_dark() is True

    def test_bei_system_entscheidet_das_betriebssystem(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_mode(Mode.SYSTEM)
        monkeypatch.setattr(theme, "system_is_dark", lambda: True)
        assert is_dark() is True
        monkeypatch.setattr(theme, "system_is_dark", lambda: False)
        assert is_dark() is False

    def test_ein_unbekannter_modus_faellt_auf_system_zurueck(self) -> None:
        """Eine Einstellungsdatei von einem neueren Stand darf nichts umwerfen."""
        set_mode("gibtesnicht")
        assert mode() is Mode.SYSTEM

    def test_umgeschaltet_liefert_das_gegenteil_des_sichtbaren(self) -> None:
        set_mode(Mode.DARK)
        assert toggled() is Mode.LIGHT
        set_mode(Mode.LIGHT)
        assert toggled() is Mode.DARK

    def test_umgeschaltet_wirkt_auch_aus_system_heraus(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sonst waere der erste Druck wirkungslos, wenn das System schon dunkel ist."""
        set_mode(Mode.SYSTEM)
        monkeypatch.setattr(theme, "system_is_dark", lambda: True)
        assert toggled() is Mode.LIGHT


class TestAkzentfarbe:
    def test_der_akzent_landet_in_den_farben(self) -> None:
        set_mode(Mode.DARK)
        set_accent("blau")
        assert colors().accent == ACCENTS["blau"][0].accent
        assert colors().accent != DARK.accent

    def test_hell_und_dunkel_haben_eigene_toene(self) -> None:
        """Ein Ton, der auf dunklem Grund traegt, wird auf hellem zu blass."""
        set_accent("blau")
        set_mode(Mode.DARK)
        auf_dunkel = colors().accent
        set_mode(Mode.LIGHT)
        assert colors().accent != auf_dunkel

    def test_der_akzent_faerbt_den_aktiven_reiter(self) -> None:
        """Die Akzentfarbe traegt die Wiedererkennung - sie muss im Stylesheet ankommen."""
        set_mode(Mode.DARK)
        set_accent("violett")
        block = build_stylesheet(colors())
        stelle = block.index("#ViewTabs::tab:selected")
        assert ACCENTS["violett"][0].accent in block[stelle : stelle + 200]

    def test_ein_unbekannter_akzent_faellt_auf_den_standard_zurueck(self) -> None:
        set_accent("neonpink")
        assert accent() == DEFAULT_ACCENT

    def test_jede_akzentfarbe_hat_einen_anzeigenamen(self) -> None:
        for sprache in ("de", "en"):
            namen = accent_names(sprache)
            assert set(namen) == set(ACCENTS)
            assert all(wert and wert != schluessel for schluessel, wert in namen.items())


class TestZoom:
    def test_der_zoom_vergroessert_die_schrift_im_stylesheet(self) -> None:
        set_zoom(DEFAULT_ZOOM)
        normal = self._groessen(build_stylesheet(colors()))
        set_zoom(150)
        gross = self._groessen(build_stylesheet(colors()))
        assert normal, "Im Stylesheet steht keine einzige Schriftgroesse"
        assert len(gross) == len(normal)
        assert all(g > n for g, n in zip(gross, normal, strict=True))

    def test_hundert_prozent_laesst_das_stylesheet_unveraendert(self) -> None:
        set_zoom(DEFAULT_ZOOM)
        assert self._groessen(build_stylesheet(colors())) == self._groessen(build_stylesheet(colors()))

    def test_der_zoom_bleibt_zwischen_den_stufen(self) -> None:
        set_zoom(5)
        assert zoom() == ZOOM_LEVELS[0]
        set_zoom(9000)
        assert zoom() == ZOOM_LEVELS[-1]

    def test_die_naechste_stufe_verlaesst_die_enden_nicht(self) -> None:
        set_zoom(ZOOM_LEVELS[-1])
        assert next_zoom(1) == ZOOM_LEVELS[-1]
        set_zoom(ZOOM_LEVELS[0])
        assert next_zoom(-1) == ZOOM_LEVELS[0]
        set_zoom(DEFAULT_ZOOM)
        assert next_zoom(1) > DEFAULT_ZOOM

    @staticmethod
    def _groessen(qss: str) -> list[int]:
        return [int(wert) for wert in re.findall(r"font-size:\s*(\d+)px", qss)]


class TestAnwenden:
    def test_ein_wechsel_faerbt_die_anwendung_um(self, app: QApplication) -> None:
        """Der Beweis am Ende der Kette: die Palette der Anwendung selbst."""
        set_mode(Mode.LIGHT)
        apply_theme(app)
        hell = app.palette().color(QPalette.ColorRole.Window).name()

        set_mode(Mode.DARK)
        apply_theme(app)
        dunkel = app.palette().color(QPalette.ColorRole.Window).name()

        assert hell != dunkel
        assert dunkel == DARK.bg_primary
        assert hell == LIGHT.bg_primary

    def test_der_akzent_landet_in_der_auswahlfarbe(self, app: QApplication) -> None:
        set_mode(Mode.DARK)
        set_accent("gruen")
        apply_theme(app)
        markiert = app.palette().color(QPalette.ColorRole.Highlight).name()
        assert markiert == ACCENTS["gruen"][0].accent

    def test_dunkel_als_argument_uebersteuert_die_einstellung(self, app: QApplication) -> None:
        """Fuer Vorschauen und Tests, ohne die Einstellung anzufassen."""
        set_mode(Mode.DARK)
        assert apply_theme(app, dunkel=False).bg_primary == LIGHT.bg_primary
        assert mode() is Mode.DARK


class TestUmschalten:
    def test_umschalten_wechselt_und_wendet_an(self, app: QApplication) -> None:
        """Der Umschalter der Werkzeugleiste - ein Aufruf, sichtbares Ergebnis."""
        from QAppFramework.theme import toggle

        set_mode(Mode.LIGHT)
        apply_theme(app)
        vorher = app.palette().color(QPalette.ColorRole.Window).name()

        neuer = toggle(app)

        assert neuer is Mode.DARK
        assert mode() is Mode.DARK
        assert app.palette().color(QPalette.ColorRole.Window).name() != vorher

    def test_zweimal_umschalten_ist_wieder_am_anfang(self, app: QApplication) -> None:
        from QAppFramework.theme import toggle

        set_mode(Mode.DARK)
        toggle(app)
        assert toggle(app) is Mode.DARK


class TestEigenesStylesheet:
    def test_eigene_regeln_lassen_sich_mitskalieren(self) -> None:
        """Eine Anwendung haengt eigene Regeln an - die muessen mitwachsen.

        Ohne das bleiben genau die auf fester Groesse, waehrend der Rest der
        Oberflaeche zoomt. Aufgefallen beim Umbau von jira-timesheet-qt.
        """
        from QAppFramework.theme import scale

        set_zoom(200)
        assert scale("#Eigen { font-size: 13px; }") == "#Eigen { font-size: 26px; }"

    def test_ohne_zoom_bleibt_der_text_wie_er_ist(self) -> None:
        from QAppFramework.theme import scale

        set_zoom(DEFAULT_ZOOM)
        eigen = "#Eigen { font-size: 13px; }"
        assert scale(eigen) == eigen
