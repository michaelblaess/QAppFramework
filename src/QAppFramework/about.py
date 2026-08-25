"""Info-Dialog.

Aufbau: farbige Kopfzone mit Name, Untertitel und Versionsmarke, darunter
Autor, Jahr und Lizenz, ein wechselndes Quote und die Verweise.

Uebernommen aus jira-timesheet-qt 0.7.2. Damit wer von einer Anwendung zur
naechsten wechselt denselben Dialog vorfindet, wird er hier gepflegt und
nicht je Anwendung nachgebaut.

Der Zitatpool liegt in `quotes/quotes.json`. Die kanonische Quelle ist
`claude-config/templates/zitate/zitate.json`, verteilt von `sync_zitate.py` -
dort stehen auch die Aufnahmeregeln. Kurz: nur gemeinfreie Autoren (der Schutz
endet 70 Jahre nach dem Tod, Paragraf 64 UrhG), jede Uebersetzung selbst
erstellt, jede Quelle benennbar. Wer ein Quote aendern will, aendert die
kanonische Datei und laesst neu verteilen - eine Aenderung hier waere beim
naechsten Lauf wieder weg.
"""

from __future__ import annotations

import json
import logging
import secrets
from dataclasses import dataclass
from importlib import resources

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .registration import (
    RegistrationMode,
    RegistrationStore,
    days_left,
    verify,
)
from .texts import pruefe_sprache, text

logger = logging.getLogger(__name__)

HOMEPAGE_URL = "https://www.michaelblaess.de/"
LIZENZ = "BUSL-1.1"

# Feste Breite: der Inhalt ist ueberschaubar, und ein Dialog, der mit der
# Laenge des gezogenen Zitats die Breite wechselt, wirkt unruhig. Die
# Beschriftungen brechen selbst um.
BREITE = 460


@dataclass(frozen=True)
class Quote:
    """Ein Quote mit Urheber und belegbarer Quelle."""

    text: str
    autor: str
    quelle: str


def load_quotes(sprache: str = "de") -> tuple[Quote, ...]:
    """Laedt den Zitatpool aus den Paketdaten.

    Args:
        sprache:
            'de' oder 'en'.

    Returns:
        Die Zitate der gewaehlten Sprache. Leer, wenn die Datei fehlt oder
        unlesbar ist - ein Info-Dialog darf daran nicht scheitern.
    """
    feld = "text_en" if pruefe_sprache(sprache) == "en" else "text_de"
    try:
        roh = (resources.files("QAppFramework") / "quotes" / "quotes.json").read_text(encoding="utf-8")
        eintraege = json.loads(roh)["zitate"]
    except Exception:
        logger.exception("Zitatpool konnte nicht geladen werden")
        return ()
    return tuple(
        Quote(text=eintrag[feld], autor=eintrag["autor"], quelle=eintrag["quelle"]) for eintrag in eintraege
    )


class AboutDialog(QDialog):
    """Zeigt Version, Lizenz, ein Quote und die Verweise."""

    def __init__(
        self,
        app_name: str,
        version: str,
        parent: QWidget | None = None,
        *,
        autor: str = "",
        jahr: str = "",
        beschreibung: str = "",
        lizenz: str = LIZENZ,
        repo_url: str = "",
        homepage_url: str | None = HOMEPAGE_URL,
        sprache: str = "de",
        zitat: Quote | None = None,
        registration_store: RegistrationStore | None = None,
        public_key: bytes | None = None,
        registration_mode: RegistrationMode = RegistrationMode.FREE,
        trial_days: int = 30,
        benefits: tuple[str, ...] = (),
    ) -> None:
        """Baut den Dialog.

        Args:
            app_name:
                Anzeigename der Anwendung, gross geschrieben - die Marke, nicht
                der Paketname.
            version:
                Versionsnummer ohne fuehrendes 'v', das setzt der Dialog.
            autor:
                Wird mit Jahr und Lizenz in einer Zeile gezeigt.
            jahr:
                Erscheinungsjahr.
            beschreibung:
                Ein Satz unter dem Namen. Nicht Autor oder Jahr wiederholen -
                die stehen schon in der Zeile darunter.
            lizenz:
                SPDX-Kennung.
            repo_url:
                Verweis auf das Repo. Leer laesst ihn weg.
            homepage_url:
                Zweiter Verweis. None laesst ihn weg.
            sprache:
                'de' oder 'en' - waehlt die Sprache des Zitats.
            registration_store:
                Ablage der Registrierung. Nur wenn sie zusammen mit dem
                oeffentlichen Schluessel angegeben wird, erscheinen Status
                und Knopf - Anwendungen ohne Registrierung bleiben, wie sie
                waren.
            public_key:
                Oeffentlicher Schluessel des Herausgebers.
            registration_mode:
                Strenge, die der Registrierungsdialog von hier aus zeigt.
            trial_days:
                Laenge des Testzeitraums, fuer die Restzeit-Angabe.
            benefits:
                Was die Registrierung bringt, fuer den Dialog.
            zitat:
                Ein festes Quote statt eines zufaelligen. Fuer Bildschirmfotos,
                die sonst bei jedem Lauf anders aussehen.
        """
        super().__init__(parent)
        self._sprache = pruefe_sprache(sprache)
        self._store = registration_store
        self._public_key = public_key
        self._registration_mode = registration_mode
        self._trial_days = trial_days
        self._benefits = benefits
        self.setWindowTitle(f"{text('about.titel', self._sprache)} {app_name}")
        self.setSizeGripEnabled(True)
        self.setFixedWidth(BREITE)

        aussen = QVBoxLayout(self)
        aussen.setContentsMargins(0, 0, 0, 0)
        aussen.setSpacing(0)
        aussen.addWidget(self._kopfzone(app_name, version, beschreibung))

        inhalt = QVBoxLayout()
        inhalt.setContentsMargins(30, 20, 30, 22)
        inhalt.setSpacing(4)
        aussen.addLayout(inhalt)

        angaben = " · ".join(teil for teil in (autor, jahr, lizenz) if teil)
        if angaben:
            zeile = QLabel(angaben)
            zeile.setObjectName("AboutFacts")
            zeile.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inhalt.addWidget(zeile)
            inhalt.addSpacing(10)

        self._registrierung_anhaengen(inhalt)
        inhalt.addSpacing(16)

        self._zitat_anhaengen(inhalt, zitat if zitat is not None else self._ziehe_zitat())

        for url in (repo_url, homepage_url):
            if not url:
                continue
            verweis = QLabel(f'<a href="{url}" style="color:palette(link);">{url}</a>')
            verweis.setObjectName("AboutLink")
            verweis.setAlignment(Qt.AlignmentFlag.AlignCenter)
            verweis.setOpenExternalLinks(True)
            verweis.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            inhalt.addWidget(verweis)

        inhalt.addSpacing(18)
        inhalt.addLayout(self._knopfzeile())

    def _registrierung_anhaengen(self, auslage: QVBoxLayout) -> None:
        """Zeigt den Stand der Registrierung und den Weg dorthin.

        Ohne Ablage und Schluessel passiert nichts - eine Anwendung ohne
        Registrierung soll den Dialog unveraendert bekommen.
        """
        if self._store is None or self._public_key is None:
            return

        self._stand = QLabel(self._standtext())
        self._stand.setObjectName("AboutRegistration")
        self._stand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stand.setWordWrap(True)
        auslage.addWidget(self._stand)

        self._registrieren = QPushButton(text("about.registrieren", self._sprache))
        self._registrieren.setObjectName("AboutRegisterButton")
        self._registrieren.clicked.connect(self._registrieren_geklickt)
        zeile = QHBoxLayout()
        zeile.addStretch(1)
        zeile.addWidget(self._registrieren)
        zeile.addStretch(1)
        auslage.addSpacing(8)
        auslage.addLayout(zeile)
        self._knopf_nachfuehren()

    def _standtext(self) -> str:
        """Registriert, im Testzeitraum, oder noch gar nichts."""
        if self._store is None or self._public_key is None:
            return ""
        stand = self._store.load()
        if verify(stand.license, self._public_key):
            mail = stand.license.email if stand.license else ""
            return text("about.registriert", self._sprache).format(mail=mail)
        rest = days_left(self._store, days=self._trial_days)
        if rest is not None:
            if rest <= 0:
                return text("about.testzeit_abgelaufen", self._sprache)
            return text("about.testzeit", self._sprache).format(tage=rest)
        return text("about.nicht_registriert", self._sprache)

    def _knopf_nachfuehren(self) -> None:
        """Wer registriert ist, braucht den Knopf nicht mehr."""
        if self._store is None or self._public_key is None:
            return
        schon = verify(self._store.load().license, self._public_key)
        self._registrieren.setVisible(not schon)

    def _registrieren_geklickt(self) -> None:
        """Oeffnet den Registrierungsdialog und fuehrt die Anzeige nach."""
        # Erst hier importiert: der Info-Dialog soll ohne den
        # Registrierungsdialog benutzbar bleiben.
        from .registration_dialog import ask_for_registration

        if self._store is None or self._public_key is None:
            return
        ask_for_registration(
            self._store,
            self._public_key,
            mode=self._registration_mode,
            days_left=days_left(self._store, days=self._trial_days),
            benefits=self._benefits,
            sprache=self._sprache,
            parent=self,
        )
        self._stand.setText(self._standtext())
        self._knopf_nachfuehren()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 - Qt-Schreibweise
        """Gibt den umbrechenden Beschriftungen die Hoehe, die ihr Text braucht.

        Ein QLabel mit Wortumbruch meldet als Wunschgroesse eine Zeile. Das
        Layout fragt heightForWidth erst, wenn die Breite feststeht - und die
        steht erst hier fest. Ohne diesen Nachschlag bekam das laengste Quote
        des Pools 43 statt der noetigen 73 Bildpunkte und war unten
        abgeschnitten (gemessen). setSizePolicy(heightForWidth) allein aendert
        daran nichts.
        """
        super().showEvent(event)
        gewachsen = False
        for beschriftung in self.findChildren(QLabel):
            if not beschriftung.wordWrap():
                continue
            noetig = beschriftung.heightForWidth(beschriftung.width())
            if noetig > beschriftung.minimumHeight():
                beschriftung.setMinimumHeight(noetig)
                gewachsen = True
        if gewachsen:
            self.adjustSize()

    def _kopfzone(self, app_name: str, version: str, beschreibung: str) -> QWidget:
        """Die farbige Zone oben - sonst steht der Dialog als weisse Flaeche da."""
        zone = QWidget()
        zone.setObjectName("AboutBanner")
        auslage = QVBoxLayout(zone)
        auslage.setContentsMargins(30, 26, 30, 24)
        auslage.setSpacing(4)

        name = QLabel(app_name)
        name.setObjectName("AboutName")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        auslage.addWidget(name)

        if beschreibung:
            untertitel = QLabel(beschreibung)
            untertitel.setObjectName("AboutBannerText")
            untertitel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            untertitel.setWordWrap(True)
            auslage.addWidget(untertitel)

        auslage.addSpacing(10)

        marke = QLabel(version)
        marke.setObjectName("AboutBadge")
        marke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zeile = QHBoxLayout()
        zeile.addStretch(1)
        zeile.addWidget(marke)
        zeile.addStretch(1)
        auslage.addLayout(zeile)
        return zone

    def _zitat_anhaengen(self, auslage: QVBoxLayout, zitat: Quote | None) -> None:
        """Haengt Quote und Urheber an. Ohne Pool bleibt der Abschnitt weg."""
        if zitat is None:
            return
        # Der Pool traegt keine Umbrueche - Daten ohne Layout. Die Beschriftung
        # bricht selbst um, der Dialog hat feste Breite.
        spruch = QLabel(zitat.text)
        spruch.setObjectName("AboutQuote")
        spruch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spruch.setWordWrap(True)
        spruch.setToolTip(zitat.quelle)
        auslage.addWidget(spruch)

        urheber = QLabel(zitat.autor)
        urheber.setObjectName("AboutQuoteAuthor")
        urheber.setAlignment(Qt.AlignmentFlag.AlignCenter)
        urheber.setToolTip(zitat.quelle)
        auslage.addWidget(urheber)
        auslage.addSpacing(18)

    def _knopfzeile(self) -> QHBoxLayout:
        zeile = QHBoxLayout()
        zeile.addStretch(1)
        schliessen = QPushButton(text("common.schliessen", self._sprache))
        schliessen.setProperty("variant", "primary")
        schliessen.setDefault(True)
        schliessen.clicked.connect(self.accept)
        zeile.addWidget(schliessen)
        zeile.addStretch(1)
        return zeile

    def _ziehe_zitat(self) -> Quote | None:
        """Waehlt ein Quote. secrets statt random, weil ruff Letzteres ruegt."""
        pool = load_quotes(self._sprache)
        return pool[secrets.randbelow(len(pool))] if pool else None
