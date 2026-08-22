"""Absturzschutz.

PySide6 leitet eine unbehandelte Ausnahme an `sys.excepthook` weiter und
beendet danach den Prozess - wortlos, wenn die Anwendung ohne Konsole laeuft.
Wer sie per Doppelklick gestartet hat, sieht nur, dass das Fenster verschwindet.

Dieser Haken zeigt stattdessen einen Dialog mit kopierbarem Bericht und laesst
den Anwender entscheiden, ob er weiterarbeitet oder beendet. In fremden
Umgebungen ist das der Unterschied zwischen einer brauchbaren Meldung und
"war auf einmal weg".

Uebernommen aus jira-timesheet-qt 0.7.2.
"""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from types import TracebackType

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .texte import pruefe_sprache, text


class FehlerDialog(QDialog):
    """Zeigt einen Fehlerbericht mit den Knoepfen Kopieren, Weiter und Beenden."""

    def __init__(self, bericht: str, parent: QWidget | None = None, *, sprache: str = "de") -> None:
        super().__init__(parent)
        self._sprache = pruefe_sprache(sprache)
        self._bericht = bericht
        self.setWindowTitle(text("absturz.titel", self._sprache))
        self.setMinimumSize(680, 460)

        auslage = QVBoxLayout(self)
        auslage.setContentsMargins(28, 24, 28, 20)
        auslage.setSpacing(10)

        kopf = QLabel(text("absturz.titel", self._sprache))
        kopf.setObjectName("DisclaimerTitle")
        auslage.addWidget(kopf)

        erklaerung = QLabel(text("absturz.erklaerung", self._sprache))
        erklaerung.setObjectName("DisclaimerText")
        erklaerung.setWordWrap(True)
        auslage.addWidget(erklaerung)

        self._ansicht = QPlainTextEdit(bericht)
        self._ansicht.setObjectName("LogView")
        self._ansicht.setReadOnly(True)
        self._ansicht.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        auslage.addWidget(self._ansicht, 1)

        knoepfe = QHBoxLayout()
        knoepfe.setSpacing(10)

        kopieren = QPushButton(text("absturz.kopieren", self._sprache))
        kopieren.setObjectName("absturz-kopieren")
        kopieren.clicked.connect(self._kopieren)
        knoepfe.addWidget(kopieren)
        knoepfe.addStretch(1)

        beenden = QPushButton(text("absturz.beenden", self._sprache))
        beenden.setObjectName("absturz-beenden")
        beenden.clicked.connect(self._beenden)
        knoepfe.addWidget(beenden)

        weiter = QPushButton(text("absturz.weiter", self._sprache))
        weiter.setObjectName("absturz-weiter")
        weiter.setProperty("variant", "primary")
        weiter.setDefault(True)
        weiter.clicked.connect(self.accept)
        knoepfe.addWidget(weiter)
        auslage.addLayout(knoepfe)

    def _kopieren(self) -> None:
        zwischenablage = QGuiApplication.clipboard()
        if zwischenablage is not None:
            zwischenablage.setText(self._bericht)

    def _beenden(self) -> None:
        self.reject()
        anwendung = QApplication.instance()
        if anwendung is not None:
            anwendung.quit()


def baue_bericht(
    art: type[BaseException],
    wert: BaseException,
    spur: TracebackType | None,
    kopfzeile: str = "",
) -> str:
    """Baut den Fehlerbericht mit Umgebungsangaben.

    Args:
        art:
            Die Ausnahmeklasse.
        wert:
            Die Ausnahme.
        spur:
            Der Aufrufstapel.
        kopfzeile:
            Name und Version der Anwendung. Ohne Angabe bleibt die Zeile weg -
            dann fehlt im Bericht aber die wichtigste Angabe fuer die
            Ursachensuche.

    Returns:
        Der Bericht, jede Zeile mit Zeilenende.
    """
    zeilen = [
        *([kopfzeile] if kopfzeile else []),
        f"Python {sys.version.split()[0]} auf {sys.platform}",
        "",
        *traceback.format_exception(art, wert, spur),
    ]
    return "".join(zeile if zeile.endswith("\n") else f"{zeile}\n" for zeile in zeilen)


def einhaengen(
    parent: QWidget | None = None,
    *,
    kopfzeile: str = "",
    sprache: str = "de",
    mitschreiben: Callable[[str], None] | None = None,
) -> None:
    """Haengt den Fehlerdialog in sys.excepthook ein.

    Args:
        parent:
            Fenster, ueber dem der Dialog erscheinen soll.
        kopfzeile:
            Name und Version der Anwendung fuer den Bericht.
        sprache:
            'de' oder 'en'.
        mitschreiben:
            Wird mit dem fertigen Bericht gerufen, bevor der Dialog erscheint -
            fuer eine Datei, die den Absturz ueberlebt. Der Bericht geht immer
            zusaetzlich auf die Fehlerausgabe.
    """
    vorheriger = sys.excepthook
    # Verhindert, dass ein Fehler im Dialog selbst eine Schleife ausloest.
    laeuft = {"wert": False}

    def behandeln(
        art: type[BaseException],
        wert: BaseException,
        spur: TracebackType | None,
    ) -> None:
        if issubclass(art, KeyboardInterrupt | SystemExit):
            # Kein Absturz, sondern eine Aufforderung zu beenden. SIGINT kommt
            # von aussen (Strg+C in der startenden Konsole, geschlossenes
            # Konsolenfenster, Abmelden) und trifft den Interpreter an einer
            # beliebigen Stelle - unter Qt fast immer in einem paintEvent, weil
            # dort die meiste Zeit verbracht wird. Ein Absturzbericht mit dieser
            # zufaelligen Zeilennummer zeigt auf unschuldigen Code und schickt
            # jeden Leser in die Irre.
            sys.stderr.write(f"{art.__name__} - Anwendung wird beendet.\n")
            anwendung = QApplication.instance()
            if anwendung is not None:
                # Ueber quit() statt hartem Abbruch, damit closeEvent laeuft:
                # Einstellungen sichern und auf laufende Faeden warten.
                anwendung.quit()
            return
        if laeuft["wert"]:
            vorheriger(art, wert, spur)
            return
        laeuft["wert"] = True
        try:
            bericht = baue_bericht(art, wert, spur, kopfzeile)
            # Immer auch auf die Fehlerausgabe, damit nichts verloren geht,
            # falls der Dialog nicht erscheinen kann.
            sys.stderr.write(bericht)
            if mitschreiben is not None:
                try:
                    mitschreiben(bericht)
                except Exception:  # noqa: BLE001 - eine kaputte Ablage darf nichts verhindern
                    sys.stderr.write("Der Bericht konnte nicht gespeichert werden.\n")
            dialog = FehlerDialog(bericht, parent, sprache=sprache)
            dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            dialog.exec()
        except Exception:  # noqa: BLE001 - der Haken darf nie selbst sprengen
            vorheriger(art, wert, spur)
        finally:
            laeuft["wert"] = False

    sys.excepthook = behandeln
