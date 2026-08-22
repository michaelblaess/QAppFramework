"""Info-Dialog.

Geprueft wird, was der Anwender sieht - und was er NICHT sehen darf: einen
abgeschnittenen Text. Der Dialog hat feste Breite, also entscheidet der Umbruch
ueber die Hoehe, und die haengt am laengsten Zitat des Pools.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Der Info-Dialog gehoert zur Desktop-Oberflaeche")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton  # noqa: E402

from QAppFramework.about import BREITE, AboutDialog, Zitat, lade_zitate  # noqa: E402
from QAppFramework.theme import anwenden  # noqa: E402

PROBE = Zitat(text="Ein kurzer Satz.", autor="Niemand", quelle="erfunden")


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    fertig = vorhanden if isinstance(vorhanden, QApplication) else QApplication([])
    anwenden(fertig, dunkel=False)
    return fertig


def _dialog(app: QApplication, **abweichend: object) -> Iterator[AboutDialog]:
    vorgabe: dict[str, object] = {
        "autor": "Michael Blaess",
        "jahr": "2026",
        "beschreibung": "Prüft Webseiten in einem Durchlauf.",
        "repo_url": "https://github.com/michaelblaess/beispiel",
        "zitat": PROBE,
    }
    vorgabe.update(abweichend)
    dialog = AboutDialog("Beispiel", "1.2.3", **vorgabe)  # type: ignore[arg-type]
    dialog.show()
    app.processEvents()
    return dialog  # type: ignore[return-value]


class TestZitatpool:
    def test_beide_sprachen_sind_vollstaendig(self) -> None:
        assert len(lade_zitate("de")) == len(lade_zitate("en")) > 0

    def test_jedes_zitat_nennt_seine_quelle(self) -> None:
        """Ohne Quelle laesst sich die Gemeinfreiheit nicht belegen."""
        for zitat in lade_zitate("de"):
            assert zitat.text.strip()
            assert zitat.autor.strip()
            assert zitat.quelle.strip()

    def test_die_texte_tragen_keine_umbrueche(self) -> None:
        """Daten ohne Layout - die Beschriftung bricht selbst um."""
        for sprache in ("de", "en"):
            assert all("\n" not in zitat.text for zitat in lade_zitate(sprache))

    def test_eine_unbekannte_sprache_ergibt_deutsch(self) -> None:
        assert lade_zitate("kl") == lade_zitate("de")

    def test_kein_geschuetzter_autor_im_pool(self) -> None:
        """Nur gemeinfreie Autoren - der Schutz endet 70 Jahre nach dem Tod (Paragraf 64 UrhG).

        Die Namen unten sind die, die inhaltlich gepasst haetten und deshalb
        immer wieder hereinrutschen. Martin Luther King ist bis Ende 2038
        geschuetzt und stand bis August 2026 fest im Code des Dialogs von
        jira-timesheet-qt.

        Der Test steht hier und nicht in den Anwendungen: der Pool liegt in
        dieser Bibliothek, ein Rueckfall traefe sonst alle gleichzeitig, und
        jede haette ihren eigenen kleinen Test - oder eben keinen.
        """
        gesperrt = (
            "martin luther king",
            "albert schweitzer",
            "c.s. lewis",
            "corrie ten boom",
            "martin fowler",
        )
        for sprache in ("de", "en"):
            for zitat in lade_zitate(sprache):
                name = zitat.autor.casefold()
                for verboten in gesperrt:
                    assert verboten not in name, f"{zitat.autor} ist nicht gemeinfrei ({sprache})"

    def test_jeder_eintrag_nennt_seine_rechtelage(self) -> None:
        """Jeder Eintrag der Paketdatei sagt, warum er verwendet werden darf."""
        import json
        from importlib import resources

        roh = (resources.files("QAppFramework") / "quotes" / "quotes.json").read_text(encoding="utf-8")
        eintraege = json.loads(roh)["zitate"]
        assert eintraege
        for eintrag in eintraege:
            assert eintrag.get("rechte", "").strip(), eintrag.get("autor")


class TestAboutDialog:
    def test_name_version_und_angaben_stehen_da(self, app: QApplication) -> None:
        dialog = _dialog(app)
        assert dialog.findChild(QLabel, "AboutName").text() == "Beispiel"  # type: ignore[union-attr]
        assert dialog.findChild(QLabel, "AboutBadge").text() == "1.2.3"  # type: ignore[union-attr]
        angaben = dialog.findChild(QLabel, "AboutFacts").text()  # type: ignore[union-attr]
        assert "Michael Blaess" in angaben
        assert "2026" in angaben
        assert "Apache-2.0" in angaben, "Michaels Vorgabelizenz fehlt"
        dialog.close()

    def test_ein_festes_zitat_wird_uebernommen(self, app: QApplication) -> None:
        """Fuer Bildschirmfotos, die sonst bei jedem Lauf anders aussehen."""
        dialog = _dialog(app)
        assert dialog.findChild(QLabel, "AboutQuote").text() == PROBE.text  # type: ignore[union-attr]
        assert dialog.findChild(QLabel, "AboutQuoteAuthor").text() == PROBE.autor  # type: ignore[union-attr]
        dialog.close()

    def test_die_quelle_steht_im_hinweis(self, app: QApplication) -> None:
        dialog = _dialog(app)
        assert dialog.findChild(QLabel, "AboutQuote").toolTip() == PROBE.quelle  # type: ignore[union-attr]
        dialog.close()

    def test_ohne_verweise_bleibt_die_zeile_weg(self, app: QApplication) -> None:
        dialog = _dialog(app, repo_url="", homepage_url=None)
        assert dialog.findChild(QLabel, "AboutLink") is None
        dialog.close()

    def test_die_verweise_oeffnen_extern(self, app: QApplication) -> None:
        """Sonst passiert beim Klick nichts, und niemand sucht den Grund."""
        dialog = _dialog(app)
        verweise = dialog.findChildren(QLabel, "AboutLink")
        assert len(verweise) == 2, "Repo und Homepage erwartet"
        assert all(v.openExternalLinks() for v in verweise)
        dialog.close()

    def test_der_schliessen_knopf_traegt_die_sprache(self, app: QApplication) -> None:
        for sprache, erwartet in (("de", "Schließen"), ("en", "Close")):
            dialog = _dialog(app, sprache=sprache)
            beschriftungen = [k.text() for k in dialog.findChildren(QPushButton)]
            assert erwartet in beschriftungen, f"{sprache}: {beschriftungen}"
            dialog.close()

    def test_das_laengste_zitat_wird_nicht_abgeschnitten(self, app: QApplication) -> None:
        """Der Dialog hat feste Breite - die Hoehe muss dem Umbruch folgen.

        Geprueft am laengsten Zitat des Pools, nicht an einem gedachten: nur
        das steht wirklich irgendwann im Fenster.
        """
        laengstes = max(lade_zitate("de"), key=lambda z: len(z.text))
        dialog = _dialog(app, zitat=laengstes)
        spruch = dialog.findChild(QLabel, "AboutQuote")
        assert spruch is not None
        assert spruch.height() >= spruch.heightForWidth(spruch.width()), (
            f"Das laengste Zitat ({len(laengstes.text)} Zeichen) passt nicht in die Hoehe"
        )
        dialog.close()

    def test_die_breite_steht_fest(self, app: QApplication) -> None:
        """Ein Dialog, der mit der Laenge des gezogenen Zitats springt, wirkt unruhig."""
        kurz = _dialog(app, zitat=PROBE)
        lang = _dialog(app, zitat=max(lade_zitate("de"), key=lambda z: len(z.text)))
        assert kurz.width() == lang.width() == BREITE
        kurz.close()
        lang.close()
