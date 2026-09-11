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
        from QAppFramework.derive import all_themes

        assert len(all_themes()) == 40
        assert all(all_themes().values())

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

    def test_die_meisten_werden_wirklich_kuerzer_gegenprobe(self) -> None:
        """Ueber ALLE, nicht nur die kuratierten - sonst ist die Stichprobe klein."""
        from QAppFramework.derive import all_themes

        lang = all_themes()
        gekuerzt = sum(1 for name, anzeige in lang.items() if anzeige.count(" ") > 1)
        assert gekuerzt >= 30

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
        assert gekuerzt >= len(lang) - 2, f"nur {gekuerzt} von {len(lang)} gekuerzt"

    def test_ein_name_ohne_trenner_bleibt_ganz(self) -> None:
        from QAppFramework.derive import short_theme_names

        assert short_theme_names()["classic-navy"] == "Classic Navy"


class TestAuswahl:
    """Alle Themes ausser denen, die Michael verworfen hat.

    Eine Ausschlussliste und keine Positivliste: er hat einzelne abgelehnt,
    nicht alle uebrigen bestaetigt.

    Und eine Liste und keine Formel. Drei Versuche, sein Urteil zu
    berechnen, sind an seiner eigenen Auswahl gescheitert - zuletzt an
    Corleone, das er gut findet.
    """

    def test_die_auswahl_ist_kleiner_als_der_bestand(self) -> None:
        from QAppFramework.derive import all_themes

        assert 0 < len(available_themes()) < len(all_themes())

    def test_jeder_ausgeschlossene_name_existiert(self) -> None:
        """Ein Tippfehler dort schliesst nichts aus und faellt sonst nicht auf."""
        from QAppFramework.derive import AUSGESCHLOSSEN, all_themes

        unbekannt = [name for name in AUSGESCHLOSSEN if name not in all_themes()]
        assert not unbekannt, unbekannt

    def test_die_ausgeschlossenen_fehlen_wirklich(self) -> None:
        from QAppFramework.derive import AUSGESCHLOSSEN

        auswahl = set(available_themes())
        assert not (auswahl & AUSGESCHLOSSEN)

    def test_beide_erscheinungsbilder_sind_vertreten(self) -> None:
        """Sonst haette ein halber Tag Auswahl gar keine."""
        arten = {palette_for_theme(name).dark for name in available_themes()}  # type: ignore[union-attr]
        assert arten == {True, False}

    def test_die_ausgeschlossenen_bleiben_im_paket(self) -> None:
        """Sie sind nur nicht waehlbar - eine gespeicherte Wahl gilt weiter."""
        assert palette_for_theme("hulkula") is not None
        assert "hulkula" not in available_themes()

    def test_ein_aktives_theme_bleibt_waehlbar(self) -> None:
        """Sonst zeigt die Oberflaeche etwas, das im Auswahlfeld fehlt.

        Beim ersten Blaettern waere es dann unwiederbringlich weg.
        """
        from QAppFramework.derive import selectable_themes

        assert "hulkula" in selectable_themes("hulkula")
        assert "hulkula" not in selectable_themes("")

    def test_ein_unbekanntes_aktives_theme_sprengt_die_liste_nicht(self) -> None:
        from QAppFramework.derive import selectable_themes

        assert selectable_themes("gibt-es-nicht") == available_themes()


class TestFarbcharakter:
    """Gehobene Farben muessen ihren Charakter behalten.

    Michael am 11.09.2026 zu Ascot und Bunty: "muss fuer Qt ueberarbeitet
    werden". Der Grund lag nicht an den Themes, sondern an der
    Hebemethode - sie mischte Weiss ein, und das entsaettigt. Aus Ascots
    sattem Dunkelgruen wurde ein blasses Graugruen, das sich vom
    Fliesstext daneben kaum noch unterschied (Abstand 28 im RGB-Raum).

    Jetzt wird zuerst ueber den Hellwert gehoben, was Farbton und
    Saettigung erhaelt, und nur wenn das Ziel damit unerreichbar bleibt
    kommt die Weissmischung dazu.
    """

    # Ein Test auf Mindestabstand zum Fliesstext stand hier und ist wieder
    # geflogen: er schlug bei Corleone an, das Michael ausdruecklich gut
    # findet. Dritter Anlauf, eine Formel fuer sein Urteil zu finden,
    # dritter Fehlschlag. Was bleibt, sind die beiden Tests unten - sie
    # pruefen, was belegt ist: dass das Heben den Farbton erhaelt.

    def test_ein_sattes_gruen_bleibt_satt(self) -> None:
        """Der Fall, an dem es aufgefallen ist."""
        import colorsys

        werte = colors_from_palette(palette_for_theme("ascot"))  # type: ignore[arg-type]
        roh = werte["green"].lstrip("#")
        kanaele = tuple(int(roh[i : i + 2], 16) / 255 for i in (0, 2, 4))
        saettigung = colorsys.rgb_to_hsv(*kanaele)[1]
        assert saettigung >= 0.5, f"Ascots Gruen ist mit {saettigung:.0%} zu blass"

    def test_das_heben_ueber_helligkeit_erhaelt_den_farbton(self) -> None:
        """Gegenprobe gegen die alte Methode.

        Weiss einzumischen haette hier eine deutlich blassere Farbe
        ergeben - der Test scheitert, wenn jemand darauf zurueckgeht.
        """
        import colorsys

        from QAppFramework.color import brighten_to_contrast, ensure_contrast

        def saettigung(hexwert: str) -> float:
            roh = hexwert.lstrip("#")
            kanaele = tuple(int(roh[i : i + 2], 16) / 255 for i in (0, 2, 4))
            return colorsys.rgb_to_hsv(*kanaele)[1]

        ueber_hsv = brighten_to_contrast("#2E7D52", "#173E2D", 4.5)
        ueber_weiss = ensure_contrast("#2E7D52", "#173E2D", 4.5)
        assert saettigung(ueber_hsv) > saettigung(ueber_weiss) + 0.2


def _abstand(erste: str, zweite: str) -> float:
    """Der Abstand zweier Farben im RGB-Raum, 0 bis 441."""
    def kanaele(hexwert: str) -> tuple[int, ...]:
        roh = hexwert.lstrip("#")
        return tuple(int(roh[i : i + 2], 16) for i in (0, 2, 4))

    a, b = kanaele(erste), kanaele(zweite)
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5
