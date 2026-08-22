"""Zell-Delegate.

Der Innenabstand laesst sich nicht behaupten, er wird gemessen: die Zelle wird
gezeichnet und im Bild nach der letzten Spalte gesucht, die nicht Hintergrund
ist. Eine Zusicherung gegen die eigene Konstante waere nur eine Wiederholung
der eigenen Rechnung - genau das war beim ersten Anlauf in jira-timesheet-qt
der Fehler.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Der Delegate gehoert zur Desktop-Oberflaeche")

from PySide6.QtCore import QRect, Qt  # noqa: E402
from PySide6.QtGui import QColor, QPainter, QPixmap, QStandardItem, QStandardItemModel  # noqa: E402
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionViewItem  # noqa: E402

from QAppFramework.zelle import ZellDelegate  # noqa: E402

BREITE, HOEHE = 200, 24
GRUND = QColor("#ffffff")


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    return vorhanden if isinstance(vorhanden, QApplication) else QApplication([])


def _gezeichnet(app: QApplication, text: str, *, rechtsbuendig: bool = True) -> QPixmap:
    """Zeichnet eine Zelle mit dem Delegate in ein Bild.

    Ueber ein echtes Modell: initStyleOption braucht einen gueltigen Index und
    holt sich Text und Ausrichtung von dort - genauso, wie es in einer Tabelle
    laeuft.
    """
    modell = QStandardItemModel(1, 1)
    eintrag = QStandardItem(text)
    eintrag.setTextAlignment(
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        if rechtsbuendig
        else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    )
    eintrag.setForeground(QColor("#000000"))
    modell.setItem(0, 0, eintrag)

    opt = QStyleOptionViewItem()
    opt.rect = QRect(0, 0, BREITE, HOEHE)
    opt.state = QStyle.StateFlag.State_Enabled | QStyle.StateFlag.State_Active

    bild = QPixmap(BREITE, HOEHE)
    bild.fill(GRUND)
    maler = QPainter(bild)
    ZellDelegate().paint(maler, opt, modell.index(0, 0))
    maler.end()
    return bild


def _letzte_bemalte_spalte(bild: QPixmap) -> int:
    """Die rechteste Bildspalte, die nicht mehr Hintergrund ist."""
    abbild = bild.toImage()
    for x in range(abbild.width() - 1, -1, -1):
        for y in range(abbild.height()):
            if QColor(abbild.pixel(x, y)) != GRUND:
                return x
    return -1


class TestInnenabstand:
    def test_der_text_klebt_nicht_an_der_rechten_kante(self, app: QApplication) -> None:
        """Qt gibt dem Zelltext vier Bildpunkte bis zur Kante - zu wenig zum Lesen."""
        ende = _letzte_bemalte_spalte(_gezeichnet(app, "1.234,50"))
        assert ende >= 0, "Es wurde gar nichts gezeichnet - misst der Test ueberhaupt?"
        abstand = BREITE - 1 - ende
        assert abstand >= 8, f"Nur {abstand} Bildpunkte bis zur Kante"

    def test_die_pruefung_kann_scheitern(self, app: QApplication) -> None:
        """Gegenprobe: ohne Delegate ist der Abstand nachweislich kleiner.

        Ohne diese Zusicherung waere der Test oben auch dann gruen, wenn er
        nichts misst.
        """
        bild = QPixmap(BREITE, HOEHE)
        bild.fill(GRUND)
        maler = QPainter(bild)
        maler.setPen(QColor("#000000"))
        maler.drawText(
            QRect(0, 0, BREITE, HOEHE),
            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            "1.234,50",
        )
        maler.end()
        assert BREITE - 1 - _letzte_bemalte_spalte(bild) < 8

    def test_linksbuendiger_text_behaelt_seinen_linken_rand(self, app: QApplication) -> None:
        """Nur rechts kuerzen: sonst fluchtet der Zelltext nicht mit der Kopfzeile."""
        abbild = _gezeichnet(app, "Beschreibung", rechtsbuendig=False).toImage()
        erste = next(
            (x for x in range(abbild.width())
             if any(QColor(abbild.pixel(x, y)) != GRUND for y in range(abbild.height()))),
            -1,
        )
        assert 0 <= erste <= 6, f"Der linke Rand betraegt {erste} Bildpunkte"

    def test_eine_leere_zelle_zeichnet_keinen_text(self, app: QApplication) -> None:
        assert _letzte_bemalte_spalte(_gezeichnet(app, "")) == -1


class TestHervorhebung:
    def test_der_treffer_wird_eingefaerbt(self) -> None:
        html = ZellDelegate.hervorhebung("Bericht erstellen", "richt")
        assert "<span style=" in html
        assert ">richt</span>" in html

    def test_ohne_begriff_bleibt_der_text_schlicht(self) -> None:
        assert ZellDelegate.hervorhebung("Bericht", "") == "Bericht"

    def test_gross_und_klein_wird_gefunden(self) -> None:
        assert "<span" in ZellDelegate.hervorhebung("Bericht", "BER")

    def test_spitze_klammern_werden_maskiert(self) -> None:
        """Sonst liest Qt den Zellinhalt als Auszeichnung - fremder Text ist kein HTML."""
        html = ZellDelegate.hervorhebung("<b>fett</b> & mehr", "")
        assert "&lt;b&gt;" in html
        assert "&amp;" in html
        assert "<b>" not in html

    def test_maskierung_greift_auch_mit_suchbegriff(self) -> None:
        html = ZellDelegate.hervorhebung("<script>x</script>", "script")
        assert "<script>" not in html
        assert "&lt;" in html

    def test_ein_treffer_mit_sonderzeichen_sprengt_das_muster_nicht(self) -> None:
        """re.escape - sonst ist ein '(' im Suchfeld ein Programmabbruch."""
        assert ZellDelegate.hervorhebung("Summe (netto)", "(netto)").count("<span") == 1

    def test_der_delegate_merkt_sich_den_begriff(self, app: QApplication) -> None:
        delegate = ZellDelegate()
        delegate.setze_suchbegriff("abc")
        assert delegate._needle == "abc"
