"""Der Registrierungsdialog.

Er sieht in allen drei Modi gleich aus - was sich unterscheidet, ist der
Untertitel und ob der Anwender ihn wegklicken darf:

- FREE:     einmalige Einladung. "Spaeter" schliesst, und es wird nie wieder
            gefragt.
- TRIAL:    bei jedem Start. "Spaeter" schliesst, solange die Frist laeuft -
            der Kopf nennt die verbleibenden Tage. Danach fuehrt nur noch ein
            Schluessel weiter.
- REQUIRED: ohne Schluessel kein Weiterkommen. Der Abbrechen-Knopf heisst dann
            "Beenden" und sagt damit, was er tut.

Eingeben laesst sich der Schluessel auf zwei Wegen: Datei auswaehlen (der
uebliche Fall - sie kommt per Mail) oder Inhalt einfuegen, falls das
Mailprogramm den Anhang verschluckt.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from .registration import (
    License,
    Registration,
    RegistrationMode,
    RegistrationStore,
    verify,
)
from .texts import pruefe_sprache, text

BREITE = 520


class RegistrationDialog(QDialog):
    """Fragt nach dem Schluessel und legt ihn ab."""

    def __init__(
        self,
        store: RegistrationStore,
        public_key: bytes,
        *,
        mode: RegistrationMode,
        days_left: int | None = None,
        benefits: tuple[str, ...] = (),
        sprache: str = "de",
        parent: QWidget | None = None,
    ) -> None:
        """Baut den Dialog.

        Args:
            store:
                Ablage, in die ein angenommener Schluessel geschrieben wird.
            public_key:
                Oeffentlicher Schluessel des Herausgebers.
            mode:
                Bestimmt Untertitel und ob sich der Dialog wegklicken laesst.
            days_left:
                Verbleibende Tage, nur im Modus TRIAL sinnvoll.
            benefits:
                Was die Registrierung bringt. Je Eintrag eine Zeile. Ohne
                Angabe entfaellt der Abschnitt - eine leere Aufzaehlung wirkt
                schwaecher als gar keine.
            sprache:
                'de' oder 'en'.
            parent:
                Elternfenster.
        """
        super().__init__(parent)
        self._store = store
        self._public_key = public_key
        self._mode = mode
        self._days_left = days_left
        self._benefits = benefits
        self._sprache = pruefe_sprache(sprache)
        self._license: License | None = None

        self.setWindowTitle(text("registrierung.titel", self._sprache))
        self.setObjectName("RegistrationDialog")
        self.setMinimumWidth(BREITE)
        self.setSizeGripEnabled(True)
        self._build()

    # --- Aufbau ----------------------------------------------------------

    def _build(self) -> None:
        aussen = QVBoxLayout(self)
        aussen.setContentsMargins(24, 20, 24, 16)
        aussen.setSpacing(12)

        titel = QLabel(text("registrierung.titel", self._sprache))
        titel.setObjectName("RegistrationTitle")
        aussen.addWidget(titel)

        untertitel = QLabel(self._untertitel())
        untertitel.setObjectName("RegistrationSubtitle")
        untertitel.setWordWrap(True)
        aussen.addWidget(untertitel)

        if self._benefits:
            vorteile = QLabel("\n".join(f"• {z}" for z in self._benefits))
            vorteile.setObjectName("RegistrationBenefits")
            vorteile.setWordWrap(True)
            aussen.addWidget(vorteile)

        aussen.addSpacing(4)

        zeile = QHBoxLayout()
        zeile.setSpacing(8)
        self._pfad = QLineEdit()
        self._pfad.setObjectName("RegistrationPath")
        self._pfad.setPlaceholderText(text("registrierung.datei_platzhalter", self._sprache))
        self._pfad.setReadOnly(True)
        zeile.addWidget(self._pfad, 1)
        self._waehlen = QPushButton(text("registrierung.datei_waehlen", self._sprache))
        self._waehlen.setObjectName("RegistrationBrowse")
        self._waehlen.clicked.connect(self._datei_waehlen)
        zeile.addWidget(self._waehlen)
        aussen.addLayout(zeile)

        einfuegen = QLabel(text("registrierung.oder_einfuegen", self._sprache))
        einfuegen.setObjectName("Hint")
        einfuegen.setWordWrap(True)
        aussen.addWidget(einfuegen)

        self._feld = QPlainTextEdit()
        self._feld.setObjectName("RegistrationKey")
        self._feld.setPlaceholderText('{"email": "...", "signature": "..."}')
        self._feld.setFixedHeight(72)
        self._feld.textChanged.connect(self._pruefen)
        aussen.addWidget(self._feld)

        self._meldung = QLabel("")
        self._meldung.setObjectName("RegistrationStatus")
        self._meldung.setWordWrap(True)
        aussen.addWidget(self._meldung)

        self._knoepfe = QDialogButtonBox()
        self._uebernehmen = self._knoepfe.addButton(
            text("registrierung.uebernehmen", self._sprache),
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self._uebernehmen.setEnabled(False)
        self._uebernehmen.clicked.connect(self._uebernehmen_geklickt)
        schluss = self._knoepfe.addButton(
            self._schlusstext(), QDialogButtonBox.ButtonRole.RejectRole
        )
        schluss.setObjectName("RegistrationDismiss")
        schluss.clicked.connect(self.reject)

        unten = QHBoxLayout()
        unten.addWidget(self._knoepfe, 1)
        unten.addWidget(QSizeGrip(self), 0, Qt.AlignmentFlag.AlignBottom)
        aussen.addLayout(unten)

    def _untertitel(self) -> str:
        """Was oben steht, haengt am Modus - und im Trial an der Restzeit."""
        if self._mode is RegistrationMode.REQUIRED:
            return text("registrierung.pflicht", self._sprache)
        if self._mode is RegistrationMode.TRIAL:
            if self._days_left is not None and self._days_left <= 0:
                return text("registrierung.abgelaufen", self._sprache)
            tage = self._days_left if self._days_left is not None else 0
            return text("registrierung.testzeit", self._sprache).format(tage=tage)
        return text("registrierung.freiwillig", self._sprache)

    def _schlusstext(self) -> str:
        """Der zweite Knopf sagt, was er tut - schliessen oder beenden."""
        abgelaufen = self._days_left is not None and self._days_left <= 0
        if self._mode is RegistrationMode.REQUIRED or (
            self._mode is RegistrationMode.TRIAL and abgelaufen
        ):
            return text("registrierung.beenden", self._sprache)
        return text("registrierung.spaeter", self._sprache)

    # --- Verhalten -------------------------------------------------------

    def _datei_waehlen(self) -> None:
        pfad, _ = QFileDialog.getOpenFileName(
            self,
            text("registrierung.datei_waehlen", self._sprache),
            "",
            "Lizenz (*.json *.lic);;Alle Dateien (*)",
        )
        if not pfad:
            return
        self._pfad.setText(pfad)
        try:
            with open(pfad, encoding="utf-8") as datei:
                self._feld.setPlainText(datei.read())
        except OSError:
            self._melde(text("registrierung.datei_fehler", self._sprache), gut=False)

    def _pruefen(self) -> None:
        """Prueft bei jeder Eingabe und faerbt die Rueckmeldung."""
        roh = self._feld.toPlainText().strip()
        if not roh:
            self._license = None
            self._uebernehmen.setEnabled(False)
            self._melde("", gut=True)
            return
        lizenz = License.from_text(roh)
        if verify(lizenz, self._public_key):
            self._license = lizenz
            self._uebernehmen.setEnabled(True)
            angabe = lizenz.email if lizenz else ""
            self._melde(
                text("registrierung.gueltig", self._sprache).format(mail=angabe), gut=True
            )
            return
        self._license = None
        self._uebernehmen.setEnabled(False)
        self._melde(text("registrierung.ungueltig", self._sprache), gut=False)

    def _melde(self, was: str, *, gut: bool) -> None:
        self._meldung.setText(was)
        self._meldung.setProperty("zustand", "gut" if gut else "schlecht")
        # Ohne das Neuberechnen greift die geaenderte Eigenschaft im Stylesheet nicht.
        stil = self._meldung.style()
        if stil is not None:
            stil.unpolish(self._meldung)
            stil.polish(self._meldung)

    def _uebernehmen_geklickt(self) -> None:
        """Legt den geprueften Schluessel ab und schliesst."""
        if self._license is None:
            return
        vorher = self._store.load()
        self._store.save(replace(vorher, license=self._license, asked=True))
        self.accept()

    @property
    def license(self) -> License | None:
        """Der uebernommene Schluessel, oder None wenn abgebrochen wurde."""
        return self._license


def ask_for_registration(
    store: RegistrationStore,
    public_key: bytes,
    *,
    mode: RegistrationMode,
    days_left: int | None = None,
    benefits: tuple[str, ...] = (),
    sprache: str = "de",
    parent: QWidget | None = None,
    dialog_factory: Callable[..., RegistrationDialog] | None = None,
) -> bool:
    """Zeigt den Dialog und sagt, ob danach ein gueltiger Schluessel vorliegt.

    Args:
        dialog_factory:
            Nur fuer Tests - ein modaler Dialog laesst sich sonst nicht
            fernhalten.

    Returns:
        True, wenn ein Schluessel uebernommen wurde.
    """
    bauen = dialog_factory or RegistrationDialog
    dialog = bauen(
        store,
        public_key,
        mode=mode,
        days_left=days_left,
        benefits=benefits,
        sprache=sprache,
        parent=parent,
    )
    dialog.exec()
    return verify(dialog.license, public_key)


__all__ = ["RegistrationDialog", "Registration", "ask_for_registration"]
