"""Der Registrierungsdialog.

Geprueft wird das Verhalten, nicht das Aussehen: dass ein gefaelschter
Schluessel den Uebernehmen-Knopf nicht freischaltet, dass der zweite Knopf im
Pflichtmodus "Beenden" heisst statt "Spaeter", und dass ein uebernommener
Schluessel wirklich in der Ablage landet.

`exec()` wird nie gerufen - ein modaler Dialog blockiert den Testlauf bis zum
Zeitablauf, und von Python aus laesst er sich nicht abfangen.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Der Dialog gehoert zur Desktop-Oberflaeche")

from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit  # noqa: E402

from QAppFramework.registration import (  # noqa: E402
    Registration,
    RegistrationMode,
    RegistrationStore,
    create_keypair,
    sign,
)
from QAppFramework.registration_dialog import (  # noqa: E402
    RegistrationDialog,
    ask_for_registration,
)


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    return vorhanden if isinstance(vorhanden, QApplication) else QApplication([])


@pytest.fixture
def ablage(tmp_path: Path) -> RegistrationStore:
    return RegistrationStore(tmp_path / "registration.json")


class TestPruefung:
    def test_ein_gueltiger_schluessel_schaltet_frei(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        privat, oeffentlich = create_keypair()
        dialog = RegistrationDialog(ablage, oeffentlich, mode=RegistrationMode.FREE)
        feld = dialog.findChild(QPlainTextEdit, "RegistrationKey")
        assert feld is not None

        assert dialog._uebernehmen.isEnabled() is False
        feld.setPlainText(sign("michael@example.com", privat).as_text())
        assert dialog._uebernehmen.isEnabled() is True
        dialog.close()

    def test_ein_gefaelschter_schluessel_schaltet_nicht_frei(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        """Der Test, auf den es ankommt - sonst waere die Signatur Zierrat."""
        fremd_privat, _ = create_keypair()
        _, echt_oeffentlich = create_keypair()
        dialog = RegistrationDialog(ablage, echt_oeffentlich, mode=RegistrationMode.FREE)
        feld = dialog.findChild(QPlainTextEdit, "RegistrationKey")
        assert feld is not None

        feld.setPlainText(sign("michael@example.com", fremd_privat).as_text())
        assert dialog._uebernehmen.isEnabled() is False
        meldung = dialog.findChild(QLabel, "RegistrationStatus")
        assert meldung is not None
        assert "nicht gültig" in meldung.text()
        dialog.close()

    def test_wirrwarr_stuerzt_nicht_ab(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(ablage, oeffentlich, mode=RegistrationMode.FREE)
        feld = dialog.findChild(QPlainTextEdit, "RegistrationKey")
        assert feld is not None
        for eingabe in ("kein json", "{}", '{"email": "a@b.de"}', "   "):
            feld.setPlainText(eingabe)
            assert dialog._uebernehmen.isEnabled() is False
        dialog.close()

    def test_uebernehmen_legt_den_schluessel_ab(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        privat, oeffentlich = create_keypair()
        dialog = RegistrationDialog(ablage, oeffentlich, mode=RegistrationMode.FREE)
        feld = dialog.findChild(QPlainTextEdit, "RegistrationKey")
        assert feld is not None
        feld.setPlainText(sign("michael@example.com", privat).as_text())
        dialog._uebernehmen_geklickt()

        gespeichert = ablage.load()
        assert gespeichert.license is not None
        assert gespeichert.license.email == "michael@example.com"
        assert gespeichert.asked is True


class TestModusAnzeige:
    def test_pflicht_nennt_den_knopf_beenden(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        """Ein Knopf soll sagen, was er tut - hier beendet er das Programm."""
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(ablage, oeffentlich, mode=RegistrationMode.REQUIRED)
        assert dialog._schlusstext() == "Beenden"
        dialog.close()

    def test_laufender_testzeitraum_nennt_ihn_spaeter(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(
            ablage, oeffentlich, mode=RegistrationMode.TRIAL, days_left=12
        )
        assert dialog._schlusstext() == "Später"
        assert "12" in dialog._untertitel()
        dialog.close()

    def test_abgelaufener_testzeitraum_nennt_ihn_beenden(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(
            ablage, oeffentlich, mode=RegistrationMode.TRIAL, days_left=0
        )
        assert dialog._schlusstext() == "Beenden"
        assert "abgelaufen" in dialog._untertitel()
        dialog.close()

    def test_freiwillig_sagt_dass_nur_einmal_gefragt_wird(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(ablage, oeffentlich, mode=RegistrationMode.FREE)
        assert "dieses eine Mal" in dialog._untertitel()
        dialog.close()

    def test_ohne_vorteile_kein_leerer_kasten(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        """Eine leere Aufzaehlung wirkt schwaecher als gar keine."""
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(ablage, oeffentlich, mode=RegistrationMode.FREE)
        assert dialog.findChild(QLabel, "RegistrationBenefits") is None
        dialog.close()

    def test_mit_vorteilen_stehen_sie_da(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(
            ablage,
            oeffentlich,
            mode=RegistrationMode.FREE,
            benefits=("Ticket-Auswertung", "Hinweis auf neue Versionen"),
        )
        kasten = dialog.findChild(QLabel, "RegistrationBenefits")
        assert kasten is not None
        assert "Ticket-Auswertung" in kasten.text()
        dialog.close()

    def test_englisch_uebersetzt_den_dialog(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        dialog = RegistrationDialog(
            ablage, oeffentlich, mode=RegistrationMode.REQUIRED, sprache="en"
        )
        assert dialog._schlusstext() == "Quit"
        assert "key is required" in dialog._untertitel()
        dialog.close()


class TestAblauf:
    def test_abbrechen_liefert_keinen_schluessel(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()

        class OhneAnzeige(RegistrationDialog):
            def exec(self) -> int:  # noqa: D102 - der modale Aufruf bleibt draussen
                return 0

        assert (
            ask_for_registration(
                ablage,
                oeffentlich,
                mode=RegistrationMode.REQUIRED,
                dialog_factory=OhneAnzeige,
            )
            is False
        )

    def test_ein_vorhandener_schluessel_wird_erkannt(
        self, app: QApplication, ablage: RegistrationStore
    ) -> None:
        privat, oeffentlich = create_keypair()
        lizenz = sign("michael@example.com", privat)
        ablage.save(Registration(license=lizenz))

        class MitEingabe(RegistrationDialog):
            def exec(self) -> int:
                feld = self.findChild(QPlainTextEdit, "RegistrationKey")
                assert feld is not None
                feld.setPlainText(lizenz.as_text())
                return 1

        assert (
            ask_for_registration(
                ablage,
                oeffentlich,
                mode=RegistrationMode.TRIAL,
                days_left=5,
                dialog_factory=MitEingabe,
            )
            is True
        )
