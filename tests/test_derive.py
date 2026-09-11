"""Jedes der 40 Themes muss eine benutzbare Oberflaeche ergeben.

Ein Terminal-Theme ist fuer drei Flaechen und Vollflaechen-Bloecke gemacht.
Eine Qt-Anwendung hat Zeilenwechselfarben, Menues, deaktivierte Zustaende,
Fokusringe. Ob eine Palette das traegt, entscheidet nicht der Augenschein,
sondern die Messung - und zwar gegen JEDEN der vier Flaechentoene.

Der Unterschied ist nicht theoretisch: eine erste Fassung der Ableitung hob
nur gegen `bg_primary`, und die inaktiven Reiter, die auf `bg_secondary`
stehen, blieben unlesbar.
"""

from __future__ import annotations

import pytest

from QAppFramework.color import contrast_ratio
from QAppFramework.derive import (
    RETRO_PALETTES,
    Palette,
    available_themes,
    colors_from_palette,
    palette_for_theme,
)
from QAppFramework.theme import Colors

FLAECHEN = ("bg_primary", "bg_secondary", "bg_tertiary", "bg_elevated")

# Dieselben Ziele wie in test_theme.py fuer die Bestandspalette. Wenn ein
# abgeleitetes Theme hier durchfaellt, ist es schlechter als das, was die
# Anwendung heute zeigt - und dann hat es im Auswahlfeld nichts verloren.
ZIELE = {
    "text_primary": 4.5,
    "text_secondary": 4.5,
    "text_tertiary": 3.0,
    "border": 1.4,
    "border_hover": 1.4,
    "accent": 3.0,
    # Die Statusfarben stehen als Text in Tabellenzellen - "erreichbar",
    # "nicht gefunden". Bis zum 11.09.2026 kamen sie ungeprueft aus dem
    # Theme und verfehlten das Ziel in ALLEN 40 Schemata.
    "green": 4.5,
    "orange": 4.5,
    "red": 4.5,
    "purple": 4.5,
}


def _werte(palette: Palette) -> dict[str, str]:
    return colors_from_palette(palette)


class TestVollstaendigkeit:
    def test_alle_vierzig_themes_kommen_an(self) -> None:
        assert len(RETRO_PALETTES) == 40

    @pytest.mark.parametrize("palette", RETRO_PALETTES, ids=lambda p: p.name)
    def test_die_werte_passen_in_colors(self, palette: Palette) -> None:
        """Der Feldsatz muss genau stimmen - kein fehlendes, kein fremdes."""
        farben = Colors(**_werte(palette))
        assert farben.bg_primary == palette.background
        assert farben.text_primary == palette.foreground

    @pytest.mark.parametrize("palette", RETRO_PALETTES, ids=lambda p: p.name)
    def test_jeder_wert_ist_eine_farbe(self, palette: Palette) -> None:
        for feld, wert in _werte(palette).items():
            if feld == "accent_subtle":
                assert wert.startswith("rgba("), f"{palette.name}.{feld} = {wert!r}"
                continue
            assert wert.startswith("#") and len(wert) == 7, f"{palette.name}.{feld} = {wert!r}"
            int(wert[1:], 16)


class TestKontrast:
    @pytest.mark.parametrize(("feld", "ziel"), sorted(ZIELE.items()))
    @pytest.mark.parametrize("palette", RETRO_PALETTES, ids=lambda p: p.name)
    def test_jede_rolle_traegt_auf_jeder_flaeche(
        self, palette: Palette, feld: str, ziel: float
    ) -> None:
        werte = _werte(palette)
        vorne = werte[feld]
        schwaechster = min(contrast_ratio(vorne, werte[f]) for f in FLAECHEN)
        assert schwaechster >= ziel, (
            f"{palette.name}: {feld} ({vorne}) erreicht nur {schwaechster:.2f} "
            f"statt {ziel} auf der schwaechsten der vier Flaechen"
        )

    @pytest.mark.parametrize("palette", RETRO_PALETTES, ids=lambda p: p.name)
    def test_der_hover_zustand_hebt_sich_von_der_ruhenden_linie_ab(self, palette: Palette) -> None:
        werte = _werte(palette)
        assert contrast_ratio(werte["border"], werte["border_hover"]) >= 1.1

    def test_die_messung_kann_scheitern(self) -> None:
        """Gegenprobe: eine Palette, deren Schrift dem Grund gleicht.

        Ohne sie belegen 240 gruene Faelle oben nichts - sie koennten auch
        gruen sein, weil der Vergleich gar nichts prueft.
        """
        flach = Palette(
            name="probe",
            primary="#202020",
            secondary="#202020",
            accent="#202020",
            foreground="#202020",
            background="#202020",
            surface="#202020",
            panel="#202020",
            boost="#202020",
            warning="#202020",
            error="#202020",
            success="#202020",
            dark=True,
        )
        werte = colors_from_palette(flach)
        # text_primary wird bewusst NICHT angehoben - es ist die Schrift des
        # Themes und der Bezug fuer alles andere. Genau deshalb faellt es hier
        # durch, und genau das soll der Test zeigen.
        schwaechster = min(contrast_ratio(werte["text_primary"], werte[f]) for f in FLAECHEN)
        assert schwaechster < 4.5


class TestAuswahl:
    def test_jedes_theme_hat_einen_anzeigenamen(self) -> None:
        namen = available_themes()
        assert len(namen) == 40
        assert all(namen.values())

    def test_die_liste_ist_nach_anzeigenamen_sortiert(self) -> None:
        werte = list(available_themes().values())
        assert werte == sorted(werte, key=str.lower)

    def test_ein_theme_laesst_sich_ueber_seinen_namen_finden(self) -> None:
        palette = palette_for_theme("brotkasten")
        assert palette is not None
        assert palette.background == "#3A2B8A"

    def test_ein_unbekannter_name_gibt_nichts_statt_zu_werfen(self) -> None:
        """Eine Einstellungsdatei kann aus einer aelteren Fassung stammen."""
        assert palette_for_theme("gibt-es-nicht") is None


class TestUnabhaengigkeit:
    def test_die_ableitung_zieht_kein_textual(self) -> None:
        """Der Grund, warum textual-themes ueberhaupt aufgeteilt wurde.

        Laeuft im eigenen Prozess: ein `import` in diesem Test wuerde sonst
        nur zeigen, dass Textual hier zufaellig nicht installiert ist.
        """
        import subprocess
        import sys

        skript = (
            "import sys\n"
            "from QAppFramework.derive import colors_from_palette, RETRO_PALETTES\n"
            "colors_from_palette(RETRO_PALETTES[0])\n"
            "geladen = [m for m in sys.modules if m == 'textual' or m.startswith('textual.')]\n"
            "assert not geladen, geladen\n"
            "print('ok')\n"
        )
        ergebnis = subprocess.run(
            [sys.executable, "-c", skript], capture_output=True, text=True, check=False
        )
        assert ergebnis.returncode == 0, ergebnis.stderr
        assert ergebnis.stdout.strip() == "ok"


class TestKurznamen:
    """Fuer Stellen mit wenig Platz - die Werkzeugleiste etwa.

    "Fifty-Eight - Black Dial, Aged Gold Lume & Bezel Red" sprengt dort
    jede vernuenftige Breite, der Name allein nicht.
    """

    def test_jedes_theme_hat_einen_kurznamen(self) -> None:
        from QAppFramework.derive import short_theme_names

        kurz = short_theme_names()
        assert set(kurz) == set(available_themes())
        assert all(kurz.values())

    def test_der_kurzname_ist_der_anfang_des_langen(self) -> None:
        from QAppFramework.derive import short_theme_names

        lang = available_themes()
        for schluessel, kurzname in short_theme_names().items():
            assert lang[schluessel].startswith(kurzname), schluessel

    def test_die_meisten_werden_wirklich_kuerzer(self) -> None:
        """Gegenprobe: gaebe die Funktion den langen Namen zurueck, waeren
        die beiden Tests oben trotzdem gruen."""
        from QAppFramework.derive import short_theme_names

        lang = available_themes()
        gekuerzt = sum(1 for s, k in short_theme_names().items() if k != lang[s])
        assert gekuerzt >= 30, f"nur {gekuerzt} von {len(lang)} gekuerzt"

    def test_ein_name_ohne_trenner_bleibt_ganz(self) -> None:
        from QAppFramework.derive import short_theme_names

        assert short_theme_names()["classic-navy"] == "Classic Navy"
