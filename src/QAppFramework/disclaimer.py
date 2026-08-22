"""Bestaetigungspflichtiger Haftungshinweis beim ersten Start.

Grundregel fuer alle Anwendungen: ohne Zustimmung laeuft das Programm nicht.

Der mitgelieferte Wortlaut beschreibt Werkzeuge, die fremde Systeme abrufen und
dabei Last erzeugen - also Scanner und Crawler. Passt das nicht, lassen sich
Titel, Einleitung und Zusicherungen ersetzen. Der HAFTUNGSABSATZ bleibt fest:
er soll ueber alle Anwendungen hinweg gleich lauten.

Wortlaut abgeglichen mit textual-widgets (Fassung 2026-07-21), damit die
Terminal- und die Desktop-Fassung derselben Anwendung dasselbe sagen.

Rechtlicher Hinweis: Der Text orientiert sich an gaengiger Praxis in
Open-Source-Projekten und laesst die nach deutschem Recht zwingenden
Haftungstatbestaende ausdruecklich unberuehrt - eine Klausel, die auch diese
ausschliesst, riskiert insgesamt unwirksam zu sein. Er ersetzt keine
Rechtsberatung.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

# Fassung des Hinweistextes. Bei inhaltlichen Aenderungen hochzaehlen - dann
# wird die Zustimmung erneut eingeholt, statt eine alte Fassung fortzuschreiben.
DISCLAIMER_VERSION = "2026-08-14"

FENSTERTITEL = "Disclaimer"
TITLE = "Nutzung auf eigene Verantwortung"

INTRO = (
    "Dieses Programm ruft Webseiten automatisiert ab und erzeugt dabei Last auf den Zielsystemen. "
    "Je nach Einstellung kann diese Last die eines normalen Besuchers um ein Vielfaches "
    "übersteigen und die Erreichbarkeit des Zielsystems beeinträchtigen."
)

DUTIES_TITLE = "Mit Ihrer Bestätigung erklären Sie:"

DUTIES: tuple[str, ...] = (
    "Sie setzen das Programm ausschließlich gegen Systeme ein, für die Ihnen eine ausdrückliche "
    "Berechtigung des Betreibers vorliegt.",
    "Sie tragen die alleinige Verantwortung für den Einsatz, die gewählten Einstellungen und alle "
    "daraus entstehenden Folgen.",
    "Vor einem Lauf gegen ein Produktivsystem prüfen Sie, ob die eingestellten Grenzwerte für "
    "dieses System angemessen sind.",
)

# FEST. Nicht je Anwendung umformulieren - der Wortlaut soll ueberall gleich
# sein. Drei getrennte Absaetze (Gewaehrleistung, Haftung, gesetzliche Grenze),
# sonst liest sich der Block als Textwand.
LIABILITY = (
    'Die Software wird unentgeltlich und ohne jede Gewährleistung bereitgestellt ("as is"), wie in '
    "Abschnitt 7 der Apache-Lizenz 2.0 beschrieben.\n\n"
    "Eine Haftung des Autors{autor} für Schäden, die aus der Nutzung entstehen, ist ausgeschlossen, "
    "soweit dies gesetzlich zulässig ist.\n\n"
    "Unberührt bleibt die Haftung für Vorsatz und grobe Fahrlässigkeit, für Schäden aus der "
    "Verletzung des Lebens, des Körpers oder der Gesundheit sowie nach dem Produkthaftungsgesetz."
)

ZUSTIMMUNG = "Ich habe den Hinweis gelesen und stimme zu"
HINWEIS = "Ohne Zustimmung kann das Programm nicht verwendet werden."


def haftungsabsatz(autor: str = "") -> str:
    """Setzt den Rechteinhaber in den Haftungsabsatz ein.

    Ohne Angabe bleibt es beim unbestimmten "des Autors", mit Angabe wird er in
    Klammern benannt - damit erkennbar ist, wer die Haftung ausschliesst.
    """
    return LIABILITY.format(autor=f" ({autor})" if autor.strip() else "")


class DisclaimerStore:
    """Haelt fest, welcher Fassung zugestimmt wurde."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    @property
    def accepted_version(self) -> str | None:
        if not self._path.is_file():
            return None
        try:
            daten = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Zustimmung konnte nicht gelesen werden")
            return None
        fassung = daten.get("accepted_version")
        return str(fassung) if fassung else None

    def record(self, version: str = DISCLAIMER_VERSION) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(
                    {"accepted_version": version, "accepted_at": datetime.now(UTC).isoformat()},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
                newline="\n",
            )
        except Exception:
            logger.exception("Zustimmung konnte nicht gespeichert werden")


class DisclaimerDialog(QDialog):
    """Zeigt den Hinweis. Ohne Haken bleibt die Zustimmung gesperrt."""

    def __init__(
        self,
        app_name: str,
        parent: QWidget | None = None,
        *,
        autor: str = "",
        title: str = TITLE,
        intro: str = INTRO,
        duties: tuple[str, ...] = DUTIES,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._intro = intro
        self._duties = duties
        self._autor = autor

        self.setWindowTitle(FENSTERTITEL)
        self.setSizeGripEnabled(True)
        self.setMinimumSize(620, 520)
        self.setModal(True)

        aussen = QVBoxLayout(self)
        aussen.setContentsMargins(20, 18, 20, 18)
        aussen.setSpacing(12)

        kopf = QLabel(f"{app_name}\n{title}")
        kopf.setObjectName("DisclaimerTitle")
        aussen.addWidget(kopf)

        aussen.addWidget(self._scrollbereich(), 1)

        self._haken = QCheckBox(ZUSTIMMUNG)
        self._haken.setObjectName("disclaimer-agree")
        self._haken.toggled.connect(self._haken_gesetzt)
        aussen.addWidget(self._haken)

        hinweis = QLabel(HINWEIS)
        hinweis.setObjectName("DisclaimerText")
        hinweis.setWordWrap(True)
        aussen.addWidget(hinweis)

        knopfzeile = QHBoxLayout()
        knopfzeile.addStretch(1)
        self._ablehnen = QPushButton("Beenden")
        self._ablehnen.setObjectName("disclaimer-quit")
        self._ablehnen.clicked.connect(self.reject)
        knopfzeile.addWidget(self._ablehnen)

        self._annehmen = QPushButton("Zustimmen und starten")
        self._annehmen.setObjectName("disclaimer-accept")
        self._annehmen.setDefault(True)
        self._annehmen.setEnabled(False)
        self._annehmen.clicked.connect(self.accept)
        knopfzeile.addWidget(self._annehmen)
        aussen.addLayout(knopfzeile)

    def _scrollbereich(self) -> QScrollArea:
        """Der Text gehoert in einen Rollbereich.

        Ein festes Layout schneidet unten ab, ohne dass man es sieht - der
        letzte Absatz waere dann unerreichbar statt nur unsichtbar.
        """
        inhalt = QWidget()
        senkrecht = QVBoxLayout(inhalt)
        senkrecht.setContentsMargins(4, 4, 12, 4)
        senkrecht.setSpacing(10)

        einleitung = QLabel(self._intro)
        einleitung.setObjectName("DisclaimerText")
        einleitung.setWordWrap(True)
        senkrecht.addWidget(einleitung)

        ueberschrift = QLabel(DUTIES_TITLE)
        ueberschrift.setObjectName("DisclaimerSection")
        ueberschrift.setWordWrap(True)
        senkrecht.addWidget(ueberschrift)

        for pflicht in self._duties:
            zeile = QLabel(f"•  {pflicht}")
            zeile.setObjectName("DisclaimerText")
            zeile.setWordWrap(True)
            senkrecht.addWidget(zeile)

        haftung = QLabel(haftungsabsatz(self._autor))
        haftung.setWordWrap(True)
        haftung.setObjectName("DisclaimerText")
        senkrecht.addWidget(haftung)
        senkrecht.addStretch(1)

        bereich = QScrollArea()
        bereich.setObjectName("DisclaimerScroll")
        bereich.setWidgetResizable(True)
        bereich.setWidget(inhalt)
        bereich.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return bereich

    def _haken_gesetzt(self, gesetzt: bool) -> None:
        self._annehmen.setEnabled(gesetzt)
