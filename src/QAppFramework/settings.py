"""Grundgeruest fuer Einstellungsdialoge.

Links eine Liste der Seiten, rechts der Inhalt, unten Abbrechen und Speichern.
Zwei Seiten bringt die Bibliothek mit - Appearance und Speicherort -, die
uebrigen liefert die Anwendung.

Was die Bibliothek bewusst NICHT kennt: wie die Anwendung ihre Einstellungen
haelt. jira-timesheet-qt hat eine getypte Klasse mit save(), SiteHammer eine
Vererbung ueber Unternehmen, Site und Umgebung in einer Datenbank. Ein
gemeinsames Datenmodell gaebe es nur um den Preis, dass beide Seiten sich
verbiegen. Der Dialog reicht deshalb nur die Darstellung heraus - alles andere
liest die Anwendung in `uebernehmen()` aus ihren eigenen Feldern.

Eine Unterklasse sieht so aus:

    class MeineEinstellungen(SettingsDialogBase):
        def __init__(self, eigene, parent=None):
            self._eigene = eigene          # VOR super().__init__ setzen
            super().__init__(darstellung_aus(eigene), parent)

        def eigene_seiten(self):
            seite, formular = self.seite("Zugang")
            self._feld = QLineEdit(self._eigene.host)
            formular.addRow(self.beschriftung("Adresse"), self._feld)
            return [("Zugang", seite)]

        def uebernehmen(self):
            self._eigene.host = self._feld.text()

        def speicherorte(self):
            return [("Einstellungen", PFAD)]

Die eigenen Felder muessen VOR `super().__init__()` stehen: der Konstruktor der
Basis ruft `eigene_seiten()` auf, und was dort gebraucht wird, muss es dann
schon geben. Andersherum bekommt man ein AttributeError mitten im Aufbau.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .color import is_light, normalize
from .texts import pruefe_sprache, text
from .theme import (
    DEFAULT_ACCENT,
    DEFAULT_ZOOM,
    ZOOM_LEVELS,
    Mode,
    accent,
    accent_names,
    mode,
    zoom,
)

# Breite eines Eingabefelds. Alle gleich, damit die rechte Kante durchgeht.
FELDBREITE = 260
# Breite der Seitenliste links.
NAVBREITE = 180
# Die Breite folgt dem breitesten Feld: Seitenliste, Beschriftung, Feld und die
# senkrechte Bildlaufleiste muessen nebeneinander passen.
MINDESTBREITE = 880
MINDESTHOEHE = 520


@dataclass(frozen=True)
class Appearance:
    """Was die Darstellungs-Seite einstellt.

    Die Anwendung speichert diese drei Werte, wie sie will - die Bibliothek
    liest sie nur beim Oeffnen und gibt sie beim Speichern zurueck.
    """

    mode: Mode = Mode.SYSTEM
    accent: str = DEFAULT_ACCENT
    zoom: int = DEFAULT_ZOOM

    @classmethod
    def aktuell(cls) -> Appearance:
        """Nimmt den Stand, der gerade gilt - fuer Anwendungen ohne eigene Ablage."""
        return cls(mode=mode(), accent=accent(), zoom=zoom())


class SettingsDialogBase(QDialog):
    """Geruest und Bausteine fuer Einstellungsdialoge."""

    def __init__(
        self,
        darstellung: Appearance | None = None,
        parent: QWidget | None = None,
        *,
        sprache: str = "de",
        titel: str = "",
    ) -> None:
        super().__init__(parent)
        self._sprache = pruefe_sprache(sprache)
        self._darstellung = darstellung if darstellung is not None else Appearance.aktuell()
        self.setWindowTitle(titel or text("einstellungen.titel", self._sprache))
        self.setMinimumSize(MINDESTBREITE, MINDESTHOEHE)
        self.setSizeGripEnabled(True)

        aussen = QVBoxLayout(self)
        aussen.setContentsMargins(0, 0, 0, 0)
        aussen.setSpacing(0)

        koerper = QHBoxLayout()
        koerper.setContentsMargins(0, 0, 0, 0)
        koerper.setSpacing(0)

        self._nav = QListWidget()
        self._nav.setObjectName("SettingsNav")
        self._nav.setFixedWidth(NAVBREITE)
        koerper.addWidget(self._nav)

        self._stapel = QStackedWidget()
        koerper.addWidget(self._stapel, 1)
        aussen.addLayout(koerper, 1)
        aussen.addWidget(self._knopfzeile())

        # Erst die Seiten der Anwendung, dann die der Bibliothek: Darstellung
        # und Speicherort gehoeren ans Ende, dort sucht sie jeder.
        for beschriftung, seite in self.eigene_seiten():
            self._seite_anhaengen(beschriftung, seite)
        self._seite_anhaengen(text("einstellungen.darstellung", self._sprache), self._seite_darstellung())
        orte = list(self.speicherorte())
        if orte:
            self._seite_anhaengen(text("einstellungen.speicherort", self._sprache), self._seite_speicherort(orte))

        self._nav.setCurrentRow(0)
        self._nav.currentRowChanged.connect(self._stapel.setCurrentIndex)

    # --- Haken fuer die Anwendung ---------------------------------------

    def eigene_seiten(self) -> Sequence[tuple[str, QWidget]]:
        """Die Seiten der Anwendung, als Paare aus Beschriftung und Widget.

        Wird aus dem Konstruktor der Basis gerufen - die eigenen Felder muessen
        also vor `super().__init__()` gesetzt sein.
        """
        return ()

    def uebernehmen(self) -> None:
        """Liest die eigenen Felder aus. Wird beim Speichern gerufen, vor accept()."""

    def darstellung_erweitern(self, formular: QFormLayout) -> None:
        """Haengt eigene Zeilen an die Darstellungs-Seite.

        Fuer alles, was fuer den Anwender zur Darstellung gehoert, aber nur
        diese eine Anwendung betrifft: Markierungsfarben, Ampelschwellen,
        Hervorhebungen. Es waere unverstaendlich, dafuer eine zweite Seite
        aufzumachen, nur weil die Bibliothek die erste haelt.

        Args:
            formular:
                Das Formular der Darstellungs-Seite, nach Erscheinungsbild,
                Akzentfarbe und Zoom.
        """

    def speicherorte(self) -> Sequence[tuple[str, Path]]:
        """Wo die Anwendung ihre Daten ablegt.

        Ergibt die Seite 'Speicherort'. Eine leere Liste laesst sie weg.
        """
        return ()

    # --- Ergebnis --------------------------------------------------------

    @property
    def darstellung(self) -> Appearance:
        """Die eingestellte Appearance. Nach dem Speichern der neue Stand."""
        return self._darstellung

    # --- Bausteine fuer die eigenen Seiten -------------------------------

    def seite(self, ueberschrift: str) -> tuple[QWidget, QFormLayout]:
        """Eine leere Seite mit Ueberschrift und Formular."""
        seite = QWidget()
        auslage = QVBoxLayout(seite)
        auslage.setContentsMargins(24, 22, 24, 22)
        auslage.setSpacing(14)

        kopf = QLabel(ueberschrift)
        kopf.setObjectName("SettingsHeading")
        auslage.addWidget(kopf)

        formular = QFormLayout()
        formular.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        formular.setHorizontalSpacing(16)
        formular.setVerticalSpacing(12)
        # Die Felder wachsen NICHT mit der Dialogbreite - sonst haetten
        # Textfelder eine andere rechte Kante als die Zahlenfelder daneben.
        formular.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        auslage.addLayout(formular)
        auslage.addStretch(1)
        return seite, formular

    @staticmethod
    def beschriftung(inhalt: str) -> QLabel:
        """Beschriftung links neben einem Feld."""
        marke = QLabel(inhalt)
        marke.setObjectName("SettingsLabel")
        marke.setMinimumWidth(120)
        return marke

    @staticmethod
    def hinweis(inhalt: str) -> QLabel:
        """Erklaerender Satz unter einem Feld.

        Ueber die volle Breite, nicht in der Feldspalte: dort waere er zu
        schmal und wuerde unten abgeschnitten.
        """
        satz = QLabel(inhalt)
        satz.setObjectName("SettingsHint")
        satz.setWordWrap(True)
        return satz

    @staticmethod
    def auswahl() -> QComboBox:
        """Auswahlliste, deren aufgeklapptes Feld dem Stylesheet folgt.

        Ohne ein ausdrueckliches QListView zeichnet Qt das Aufklappfeld mit
        einer eigenen Ansicht, die die ::item-Regeln uebergeht - die Auswahl
        erschiene dann im Systemblau statt in der Akzentfarbe.
        """
        feld = QComboBox()
        feld.setView(QListView())
        feld.setFixedWidth(FELDBREITE)
        # Ohne das behaelt die Liste die Breite, die sie beim ersten Anzeigen
        # hatte, und spaeter eingefuegte laengere Eintraege werden gekuerzt.
        feld.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        return feld

    def farbknopf(self, hexwert: str, titel: str = "") -> QPushButton:
        """Ein Knopf, der seine Farbe zeigt und beim Klick den Farbwaehler oeffnet.

        Der gewaehlte Wert steht danach in `knopf.property("farbe")`.

        Args:
            hexwert:
                Startwert, mit oder ohne Doppelkreuz.
            titel:
                Fensterzeile des Farbwaehlers.

        Returns:
            Der Knopf.
        """
        knopf = QPushButton()
        knopf.setFixedWidth(FELDBREITE)
        knopf.setCursor(Qt.CursorShape.PointingHandCursor)
        self._farbe_setzen(knopf, normalize(hexwert))
        knopf.clicked.connect(lambda: self._farbe_waehlen(knopf, titel))
        return knopf

    @staticmethod
    def farbe_von(knopf: QPushButton) -> str:
        """Der Wert eines Farbknopfs als RRGGBB."""
        return str(knopf.property("farbe") or "")

    def pfadzeile(self, pfad: Path) -> QWidget:
        """Zeigt einen Pfad und oeffnet ihn auf Klick im Dateimanager."""
        zeile = QWidget()
        auslage = QHBoxLayout(zeile)
        auslage.setContentsMargins(0, 0, 0, 0)
        auslage.setSpacing(8)

        wert = QLabel(str(pfad))
        wert.setObjectName("SettingsPath")
        wert.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        auslage.addWidget(wert, 1)

        knopf = QPushButton(text("einstellungen.oeffnen", self._sprache))
        knopf.setProperty("variant", "secondary")
        knopf.setCursor(Qt.CursorShape.PointingHandCursor)
        knopf.clicked.connect(lambda: self.oeffne(pfad))
        auslage.addWidget(knopf)
        return zeile

    @staticmethod
    def oeffne(pfad: Path) -> None:
        """Oeffnet das Verzeichnis eines Pfads im Dateimanager."""
        ziel = pfad if pfad.is_dir() else pfad.parent
        if not ziel.exists():
            ziel.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(ziel)))

    # --- Innenleben ------------------------------------------------------

    def _seite_anhaengen(self, beschriftung: str, seite: QWidget) -> None:
        self._nav.addItem(beschriftung)
        self._stapel.addWidget(self._scrollbar(seite))

    @staticmethod
    def _scrollbar(seite: QWidget) -> QWidget:
        """Haengt eine Seite in einen Bildlaufbereich.

        Ohne den wird eine Seite, die hoeher ist als der Dialog, nicht nur
        abgeschnitten - der untere Teil ist UNERREICHBAR, weil ein
        QStackedWidget nicht scrollt.
        """
        bereich = QScrollArea()
        bereich.setObjectName("SettingsScroll")
        bereich.setWidget(seite)
        # Ohne das behaelt die Seite ihre Wunschbreite, und der Bereich zeigt
        # eine waagerechte Bildlaufleiste statt die Seite mitzuziehen.
        bereich.setWidgetResizable(True)
        bereich.setFrameShape(QScrollArea.Shape.NoFrame)
        return bereich

    def _seite_darstellung(self) -> QWidget:
        seite, formular = self.seite(text("einstellungen.darstellung", self._sprache))

        self._feld_modus = self.auswahl()
        for eintrag in (Mode.SYSTEM, Mode.DARK, Mode.LIGHT):
            self._feld_modus.addItem(text(f"mode.{eintrag.value}", self._sprache), eintrag.value)
        self._feld_modus.setCurrentIndex(max(0, self._feld_modus.findData(self._darstellung.mode.value)))
        formular.addRow(self.beschriftung(text("einstellungen.erscheinungsbild", self._sprache)), self._feld_modus)

        self._feld_akzent = self.auswahl()
        for schluessel, anzeige in sorted(accent_names(self._sprache).items(), key=lambda paar: paar[1]):
            self._feld_akzent.addItem(anzeige, schluessel)
        self._feld_akzent.setCurrentIndex(max(0, self._feld_akzent.findData(self._darstellung.accent)))
        formular.addRow(self.beschriftung(text("einstellungen.akzentfarbe", self._sprache)), self._feld_akzent)

        self._feld_zoom = self.auswahl()
        for stufe in ZOOM_LEVELS:
            self._feld_zoom.addItem(f"{stufe} %", stufe)
        self._feld_zoom.setCurrentIndex(max(0, self._feld_zoom.findData(self._darstellung.zoom)))
        formular.addRow(self.beschriftung(text("einstellungen.zoom", self._sprache)), self._feld_zoom)

        self.darstellung_erweitern(formular)
        formular.addRow(self.hinweis(text("einstellungen.sofort", self._sprache)))
        return seite

    def _seite_speicherort(self, orte: Sequence[tuple[str, Path]]) -> QWidget:
        seite, formular = self.seite(text("einstellungen.speicherort", self._sprache))
        # Anders als bei den Eingabeseiten sollen die Zeilen die volle Breite
        # fuellen - nur so stehen die Oeffnen-Knoepfe buendig untereinander
        # statt an jeder Pfadlaenge ausgerichtet.
        formular.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        for beschriftung, pfad in orte:
            formular.addRow(self.beschriftung(beschriftung), self.pfadzeile(pfad))
        formular.addRow(self.hinweis(text("einstellungen.ortehinweis", self._sprache)))
        return seite

    def _knopfzeile(self) -> QWidget:
        zeile = QWidget()
        zeile.setObjectName("DialogButtons")
        auslage = QHBoxLayout(zeile)
        auslage.setContentsMargins(24, 14, 24, 16)
        auslage.setSpacing(10)
        auslage.addStretch(1)

        abbrechen = QPushButton(text("einstellungen.abbrechen", self._sprache))
        abbrechen.setObjectName("SettingsCancel")
        abbrechen.clicked.connect(self.reject)
        auslage.addWidget(abbrechen)

        speichern = QPushButton(text("einstellungen.speichern", self._sprache))
        speichern.setObjectName("SettingsSave")
        speichern.setProperty("variant", "primary")
        speichern.setDefault(True)
        speichern.clicked.connect(self._speichern)
        auslage.addWidget(speichern)
        return zeile

    def _speichern(self) -> None:
        """Sammelt die Darstellung ein, laesst die Anwendung ihre Felder lesen, schliesst."""
        self._darstellung = Appearance(
            mode=Mode(str(self._feld_modus.currentData())),
            accent=str(self._feld_akzent.currentData()),
            zoom=int(self._feld_zoom.currentData()),
        )
        self.uebernehmen()
        self.accept()

    def _farbe_waehlen(self, knopf: QPushButton, titel: str) -> None:
        gewaehlt = QColorDialog.getColor(QColor(f"#{self.farbe_von(knopf)}"), self, titel)
        if gewaehlt.isValid():
            self._farbe_setzen(knopf, normalize(gewaehlt.name()))

    @staticmethod
    def _farbe_setzen(knopf: QPushButton, hexwert: str) -> None:
        """Malt die Farbe auf den Knopf und legt sie als Eigenschaft ab.

        Die Schriftfarbe richtet sich nach der Helligkeit - sonst steht auf
        einem dunklen Rot schwarze Schrift, die niemand lesen kann.
        """
        knopf.setProperty("farbe", hexwert)
        knopf.setText(f"#{hexwert}")
        schrift = "#000000" if is_light(hexwert) else "#ffffff"
        knopf.setStyleSheet(
            f"background-color: #{hexwert}; color: {schrift};"
            " border: 1px solid rgba(0,0,0,0.25); border-radius: 4px; padding: 5px 10px;"
        )
