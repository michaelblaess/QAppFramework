"""Der Haftungshinweis muss anpassbar sein - bis auf den Haftungsabsatz."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402

from handmade_qt.disclaimer import (  # noqa: E402
    DISCLAIMER_VERSION,
    DUTIES,
    DisclaimerDialog,
    DisclaimerStore,
    haftungsabsatz,
)


@pytest.fixture(scope="session")
def anwendung() -> Iterator[QApplication]:
    app = QApplication.instance() or QApplication([])
    yield app  # type: ignore[misc]


def _texte(dialog: DisclaimerDialog) -> list[str]:
    return [beschriftung.text() for beschriftung in dialog.findChildren(QLabel)]


class TestSpeicher:
    def test_ohne_datei_gibt_es_keine_zustimmung(self, tmp_path: Path) -> None:
        assert DisclaimerStore(tmp_path / "d.json").accepted_version is None

    def test_zustimmung_ueberlebt_den_neustart(self, tmp_path: Path) -> None:
        DisclaimerStore(tmp_path / "d.json").record()
        assert DisclaimerStore(tmp_path / "d.json").accepted_version == DISCLAIMER_VERSION

    def test_eine_kaputte_datei_gilt_als_keine_zustimmung(self, tmp_path: Path) -> None:
        datei = tmp_path / "d.json"
        datei.write_text("{kein json", encoding="utf-8")
        assert DisclaimerStore(datei).accepted_version is None


class TestDialog:
    def test_zustimmen_ist_ohne_haken_gesperrt(self, anwendung: QApplication) -> None:
        dialog = DisclaimerDialog("my-tool 1.0")
        assert not dialog._annehmen.isEnabled()
        dialog._haken.setChecked(True)
        assert dialog._annehmen.isEnabled()

    def test_die_fensterzeile_heisst_disclaimer(self, anwendung: QApplication) -> None:
        assert DisclaimerDialog("my-tool 1.0").windowTitle() == "Disclaimer"

    def test_der_standardtext_beschreibt_abrufende_werkzeuge(self, anwendung: QApplication) -> None:
        texte = " ".join(_texte(DisclaimerDialog("my-tool 1.0")))
        assert "Last auf den Zielsystemen" in texte
        for pflicht in DUTIES:
            assert pflicht in texte


class TestAnpassbarkeit:
    """Anwendungen mit anderem Zweck muessen den Text ersetzen koennen."""

    def test_eigene_zusicherungen_ersetzen_die_vorgabe(self, anwendung: QApplication) -> None:
        eigen = ("Diese Anwendung tut etwas ganz anderes.",)
        texte = " ".join(_texte(DisclaimerDialog("my-tool 1.0", duties=eigen)))
        assert eigen[0] in texte
        assert DUTIES[0] not in texte

    def test_der_haftungsabsatz_bleibt_auch_dann_stehen(self, anwendung: QApplication) -> None:
        """Er soll ueber alle Anwendungen hinweg gleich lauten."""
        texte = " ".join(_texte(DisclaimerDialog("my-tool 1.0", duties=("etwas anderes",))))
        assert "ohne jede Gewährleistung" in texte
        assert "Produkthaftungsgesetz" in texte

    def test_der_rechteinhaber_wird_eingesetzt(self) -> None:
        assert "des Autors (Michael Blaess)" in haftungsabsatz("Michael Blaess")
        assert "des Autors für" in haftungsabsatz("")
