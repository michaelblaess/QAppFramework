"""Absturzschutz.

Der Haken ist die letzte Instanz: greift er nicht, verschwindet das Fenster
wortlos, und der Anwender hat nichts in der Hand. Geprueft wird deshalb, dass
er wirklich in sys.excepthook haengt, dass der Bericht die Ursache nennt und
dass ein Abbruch von aussen NICHT als Absturz gemeldet wird.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
from collections.abc import Iterator

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Der Fehlerdialog gehoert zur Desktop-Oberflaeche")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton  # noqa: E402

from QAppFramework.absturz import (  # noqa: E402
    FehlerDialog,
    abbruch_abfangen,
    baue_bericht,
    einhaengen,
)
from QAppFramework.theme import anwenden  # noqa: E402


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    fertig = vorhanden if isinstance(vorhanden, QApplication) else QApplication([])
    anwenden(fertig, dunkel=False)
    return fertig


@pytest.fixture(autouse=True)
def _haken_zuruecksetzen() -> Iterator[None]:
    """sys.excepthook ist global - ohne Zuruecksetzen faengt er die ganze Suite ab."""
    vorher = sys.excepthook
    yield
    sys.excepthook = vorher


def _ausnahme() -> tuple[type[BaseException], BaseException, object]:
    try:
        raise ValueError("etwas ist schiefgelaufen")
    except ValueError:
        art, wert, spur = sys.exc_info()
        assert art is not None and wert is not None
        return art, wert, spur


class TestBericht:
    def test_der_bericht_nennt_die_ursache(self) -> None:
        art, wert, spur = _ausnahme()
        bericht = baue_bericht(art, wert, spur)  # type: ignore[arg-type]
        assert "ValueError" in bericht
        assert "etwas ist schiefgelaufen" in bericht
        assert "_ausnahme" in bericht, "Der Aufrufstapel fehlt"

    def test_die_kopfzeile_steht_ganz_oben(self) -> None:
        """Ohne Name und Version ist ein weitergegebener Bericht wenig wert."""
        art, wert, spur = _ausnahme()
        bericht = baue_bericht(art, wert, spur, "Beispiel 1.2.3")  # type: ignore[arg-type]
        assert bericht.splitlines()[0] == "Beispiel 1.2.3"

    def test_die_umgebung_steht_dabei(self) -> None:
        art, wert, spur = _ausnahme()
        bericht = baue_bericht(art, wert, spur)  # type: ignore[arg-type]
        assert sys.version.split()[0] in bericht
        assert sys.platform in bericht

    def test_jede_zeile_endet_mit_einem_umbruch(self) -> None:
        """Sonst kleben Kopfzeile und Aufrufstapel aneinander."""
        art, wert, spur = _ausnahme()
        bericht = baue_bericht(art, wert, spur, "Beispiel 1.2.3")  # type: ignore[arg-type]
        assert bericht.endswith("\n")
        assert "\n\n" in bericht, "Zwischen Umgebung und Aufrufstapel fehlt die Leerzeile"


class TestDialog:
    def test_der_bericht_steht_lesbar_im_dialog(self, app: QApplication) -> None:
        dialog = FehlerDialog("Zeile eins\nZeile zwei")
        ansicht = dialog.findChild(QPlainTextEdit, "LogView")
        assert ansicht is not None
        assert ansicht.toPlainText() == "Zeile eins\nZeile zwei"
        assert ansicht.isReadOnly(), "Ein Bericht, den man versehentlich aendert, ist wertlos"
        dialog.close()

    def test_alle_drei_knoepfe_sind_da(self, app: QApplication) -> None:
        dialog = FehlerDialog("x")
        namen = {k.objectName() for k in dialog.findChildren(QPushButton)}
        assert namen == {"absturz-kopieren", "absturz-beenden", "absturz-weiter"}
        dialog.close()

    def test_kopieren_legt_den_bericht_in_die_zwischenablage(self, app: QApplication) -> None:
        from PySide6.QtGui import QGuiApplication

        dialog = FehlerDialog("der ganze Bericht")
        knopf = dialog.findChild(QPushButton, "absturz-kopieren")
        assert knopf is not None
        knopf.click()
        zwischenablage = QGuiApplication.clipboard()
        assert zwischenablage is not None
        assert zwischenablage.text() == "der ganze Bericht"
        dialog.close()

    def test_englisch_uebersetzt_die_knoepfe(self, app: QApplication) -> None:
        dialog = FehlerDialog("x", sprache="en")
        beschriftungen = {k.text() for k in dialog.findChildren(QPushButton)}
        assert beschriftungen == {"Copy report", "Quit", "Carry on"}
        dialog.close()


class TestEinhaengen:
    def test_der_haken_haengt_danach_in_excepthook(self) -> None:
        vorher = sys.excepthook
        einhaengen()
        assert sys.excepthook is not vorher

    def test_ein_abbruch_von_aussen_gilt_nicht_als_absturz(
        self, app: QApplication, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Strg+C trifft den Interpreter an beliebiger Stelle - unter Qt fast
        immer in einem paintEvent. Ein Bericht mit dieser Zeilennummer zeigt auf
        unschuldigen Code.
        """
        gesehen: list[str] = []
        einhaengen(mitschreiben=gesehen.append)
        sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
        assert gesehen == [], "Ein Abbruch von aussen darf keinen Bericht erzeugen"
        assert "KeyboardInterrupt" in capsys.readouterr().err

    def test_der_bericht_wird_mitgeschrieben(self, app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ohne Ablage ueberlebt der Bericht das Schliessen des Dialogs nicht."""
        gesehen: list[str] = []
        # Der Dialog wuerde blockieren - hier geht es nur um den Weg davor.
        monkeypatch.setattr(FehlerDialog, "exec", lambda self: 0)
        einhaengen(kopfzeile="Beispiel 1.2.3", mitschreiben=gesehen.append)
        art, wert, spur = _ausnahme()
        sys.excepthook(art, wert, spur)  # type: ignore[arg-type]
        assert len(gesehen) == 1
        assert "etwas ist schiefgelaufen" in gesehen[0]
        assert gesehen[0].startswith("Beispiel 1.2.3")

    def test_eine_kaputte_ablage_verschluckt_den_bericht_nicht(
        self, app: QApplication, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Wenn schon das Speichern scheitert, muss wenigstens stderr etwas haben."""

        def kaputt(_bericht: str) -> None:
            raise OSError("Platte voll")

        monkeypatch.setattr(FehlerDialog, "exec", lambda self: 0)
        einhaengen(mitschreiben=kaputt)
        art, wert, spur = _ausnahme()
        sys.excepthook(art, wert, spur)  # type: ignore[arg-type]
        fehlerausgabe = capsys.readouterr().err
        assert "etwas ist schiefgelaufen" in fehlerausgabe
        assert "nicht gespeichert" in fehlerausgabe


class TestAbbruchAbfangen:
    """Strg+C muss die Schleife verlassen, nicht irgendwo eine Ausnahme werfen."""

    @pytest.fixture(autouse=True)
    def _behandler_zuruecksetzen(self) -> Iterator[None]:
        vorher = signal.getsignal(signal.SIGINT)
        yield
        signal.signal(signal.SIGINT, vorher)

    def test_strg_c_beendet_die_schleife_zuegig(self, app: QApplication) -> None:
        """Der Kern der Sache, und er kann scheitern.

        Ohne den Wecker in `abbruch_abfangen` kommt der Behandler nie an die
        Reihe, solange Qt in seiner eigenen Schleife wartet - dann greift erst
        die Notbremse und die gemessene Zeit reisst die Schranke.
        """
        wecker = abbruch_abfangen(app, takt_ms=50)
        notbremse = QTimer()
        notbremse.setSingleShot(True)
        notbremse.timeout.connect(app.quit)
        notbremse.start(3000)

        # Aus einem Nebenlaeufer, damit SIGINT die wartende Schleife trifft und
        # nicht zufaellig gerade laufenden Python-Code.
        threading.Timer(0.3, lambda: signal.raise_signal(signal.SIGINT)).start()
        begonnen = time.monotonic()
        app.exec()
        gebraucht = time.monotonic() - begonnen

        wecker.stop()
        notbremse.stop()
        assert gebraucht < 1.5, f"Strg+C wirkte erst nach {gebraucht:.2f}s"

    def test_der_behandler_haengt_am_signal(self, app: QApplication) -> None:
        """Ohne eigenen Behandler wuerde SIGINT zu einem KeyboardInterrupt."""
        wecker = abbruch_abfangen(app)
        try:
            assert signal.getsignal(signal.SIGINT) is not signal.default_int_handler
        finally:
            wecker.stop()

    def test_der_wecker_haengt_an_der_anwendung(self, app: QApplication) -> None:
        """Sonst raeumt Python ihn ab und der Behandler kommt nie an die Reihe."""
        wecker = abbruch_abfangen(app)
        try:
            assert wecker.parent() is app
            assert wecker.isActive()
        finally:
            wecker.stop()

    def test_die_meldung_nennt_den_grund(
        self, app: QApplication, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Wer in der Konsole Strg+C drueckt, soll eine Bestaetigung sehen."""
        wecker = abbruch_abfangen(app)
        try:
            behandler = signal.getsignal(signal.SIGINT)
            assert callable(behandler)
            behandler(signal.SIGINT, None)
            assert "Anwendung wird beendet" in capsys.readouterr().err
        finally:
            wecker.stop()
