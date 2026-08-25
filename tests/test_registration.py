"""Registrierung und Testzeitraum.

Der Kern kommt ohne Qt aus, deshalb laeuft hier alles ohne Fenster. Geprueft
wird, was wirklich traegt: dass eine gefaelschte Unterschrift auffliegt, dass
die zurueckgestellte Uhr den Testzeitraum nicht verlaengert, und dass ein
selbst gebautes Programm niemanden aussperrt.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from QAppFramework.registration import (
    License,
    Registration,
    RegistrationStore,
    TrialState,
    create_keypair,
    days_left,
    normalize_email,
    record_launch,
    sign,
    start_trial,
    trial_expired,
    verify,
)
from QAppFramework.registration import (
    RegistrationMode as Mode,
)
from QAppFramework.registration import (
    RegistrationOutcome as Outcome,
)
from QAppFramework.registration import (
    check_registration as check,
)

JETZT = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)


@pytest.fixture
def schluessel() -> tuple[bytes, bytes]:
    return create_keypair()


@pytest.fixture
def ablage(tmp_path: Path) -> RegistrationStore:
    return RegistrationStore(tmp_path / "registration.json")


class TestSignatur:
    def test_ein_ausgestellter_schluessel_wird_angenommen(
        self, schluessel: tuple[bytes, bytes]
    ) -> None:
        privat, oeffentlich = schluessel
        assert verify(sign("michael@example.com", privat), oeffentlich)

    def test_eine_andere_mail_faellt_durch(self, schluessel: tuple[bytes, bytes]) -> None:
        """Der Kern der Sache: die Unterschrift gilt genau einer Adresse."""
        privat, oeffentlich = schluessel
        lizenz = sign("michael@example.com", privat)
        gefaelscht = License(email="jemand@example.com", signature=lizenz.signature)
        assert verify(gefaelscht, oeffentlich) is False

    def test_eine_erfundene_unterschrift_faellt_durch(
        self, schluessel: tuple[bytes, bytes]
    ) -> None:
        _, oeffentlich = schluessel
        assert verify(License(email="michael@example.com", signature=bytes(64)), oeffentlich) is False

    def test_ein_fremdes_schluesselpaar_faellt_durch(self) -> None:
        """Ohne den privaten Schluessel des Herausgebers geht gar nichts.

        Das ist der Unterschied zu einer berechneten Nummer: wer den
        Algorithmus aus dem Programm holt, kann damit nichts erzeugen.
        """
        fremd_privat, _ = create_keypair()
        _, echt_oeffentlich = create_keypair()
        assert verify(sign("michael@example.com", fremd_privat), echt_oeffentlich) is False

    def test_gross_klein_und_leerzeichen_stoeren_nicht(
        self, schluessel: tuple[bytes, bytes]
    ) -> None:
        privat, oeffentlich = schluessel
        lizenz = sign("  Michael@Example.COM ", privat)
        assert verify(lizenz, oeffentlich)
        assert normalize_email(lizenz.email) == "michael@example.com"

    def test_die_lizenzdatei_ueberlebt_hin_und_zurueck(
        self, schluessel: tuple[bytes, bytes]
    ) -> None:
        privat, oeffentlich = schluessel
        lizenz = sign("michael@example.com", privat)
        assert verify(License.from_text(lizenz.as_text()), oeffentlich)

    def test_kaputte_lizenzdatei_stuerzt_nicht_ab(self) -> None:
        assert License.from_text("kein json") is None
        assert License.from_text('{"email": "a@b.de"}') is None


class TestTestzeitraum:
    def test_zurueckgestellte_uhr_verlaengert_nicht(self) -> None:
        """Der eigentliche Riegel - und der Test faellt ohne ihn.

        Wer die Systemzeit zurueckdreht, bekommt keinen frischen Testzeitraum,
        sondern einen abgelaufenen.
        """
        stand = TrialState(
            first_seen=JETZT - timedelta(days=20),
            latest_seen=JETZT,
            launches=5,
        )
        zurueckgedreht = JETZT - timedelta(days=15)
        assert stand.clock_turned_back(zurueckgedreht)
        assert trial_expired(stand, zurueckgedreht, days=30, max_launches=60)

    def test_kleine_zeitspruenge_sperren_niemanden_aus(self) -> None:
        """Zeitzonen und Zeitabgleich duerfen keinen ehrlichen Anwender treffen."""
        stand = start_trial(JETZT)
        assert stand.clock_turned_back(JETZT - timedelta(seconds=30)) is False

    def test_der_hoechste_zeitpunkt_sinkt_nie(self) -> None:
        stand = record_launch(start_trial(JETZT), JETZT - timedelta(days=5))
        assert stand.latest_seen == JETZT

    def test_die_tage_laufen_ab(self) -> None:
        stand = start_trial(JETZT - timedelta(days=31))
        assert trial_expired(stand, JETZT, days=30, max_launches=60)

    def test_zu_viele_starts_laufen_ab(self) -> None:
        """Zweite Schranke, unabhaengig von jeder Uhr."""
        stand = TrialState(first_seen=JETZT, latest_seen=JETZT, launches=61)
        assert trial_expired(stand, JETZT, days=30, max_launches=60)

    def test_frischer_testzeitraum_laeuft(self) -> None:
        assert trial_expired(start_trial(JETZT), JETZT, days=30, max_launches=60) is False


class TestAblauf:
    def test_selbst_gebaut_laeuft_immer_durch(self, ablage: RegistrationStore) -> None:
        """Die Lizenz erlaubt Selbstbauern die Nutzung - dann darf die Pruefung
        sie nicht aussperren, auch nicht im strengsten Modus."""
        _, oeffentlich = create_keypair()
        ergebnis = check(ablage, oeffentlich, mode=Mode.REQUIRED, enforced=False, now=JETZT)
        assert ergebnis is Outcome.CONTINUE

    def test_ohne_schluessel_und_pflicht_ist_schluss(self, ablage: RegistrationStore) -> None:
        _, oeffentlich = create_keypair()
        assert check(ablage, oeffentlich, mode=Mode.REQUIRED, now=JETZT) is Outcome.QUIT

    def test_ohne_schluessel_und_frei_nur_ein_hinweis(self, ablage: RegistrationStore) -> None:
        _, oeffentlich = create_keypair()
        assert check(ablage, oeffentlich, mode=Mode.FREE, now=JETZT) is Outcome.REMIND

    def test_mit_schluessel_ist_der_modus_egal(
        self, ablage: RegistrationStore, schluessel: tuple[bytes, bytes]
    ) -> None:
        privat, oeffentlich = schluessel
        ablage.save(Registration(license=sign("michael@example.com", privat)))
        for modus in Mode:
            assert check(ablage, oeffentlich, mode=modus, now=JETZT) is Outcome.CONTINUE

    def test_der_testzeitraum_beginnt_beim_ersten_start(
        self, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        assert check(ablage, oeffentlich, mode=Mode.TRIAL, now=JETZT) is Outcome.REMIND
        stand = ablage.load()
        assert stand.trial is not None
        assert stand.trial.first_seen == JETZT
        assert stand.trial.launches == 1

    def test_der_testzeitraum_endet(self, ablage: RegistrationStore) -> None:
        _, oeffentlich = create_keypair()
        check(ablage, oeffentlich, mode=Mode.TRIAL, now=JETZT)
        spaeter = JETZT + timedelta(days=31)
        assert check(ablage, oeffentlich, mode=Mode.TRIAL, now=spaeter) is Outcome.QUIT

    def test_die_uhr_zurueckstellen_hilft_nicht(self, ablage: RegistrationStore) -> None:
        """Der Ablauf von Anfang bis Ende, so wie ein Anwender es versuchen wuerde."""
        _, oeffentlich = create_keypair()
        check(ablage, oeffentlich, mode=Mode.TRIAL, now=JETZT)
        # Nach 31 Tagen ist Schluss.
        spaet = JETZT + timedelta(days=31)
        assert check(ablage, oeffentlich, mode=Mode.TRIAL, now=spaet) is Outcome.QUIT
        # Uhr zurueck auf den Anfang - und es bleibt Schluss.
        assert check(ablage, oeffentlich, mode=Mode.TRIAL, now=JETZT) is Outcome.QUIT

    def test_die_datei_darf_fehlen(self, tmp_path: Path) -> None:
        leer = RegistrationStore(tmp_path / "gibt-es-nicht" / "registration.json")
        assert leer.load() == Registration()

    def test_verbleibende_tage(self, ablage: RegistrationStore) -> None:
        _, oeffentlich = create_keypair()
        check(ablage, oeffentlich, mode=Mode.TRIAL, now=JETZT)
        assert days_left(ablage, days=30, now=JETZT + timedelta(days=10)) == 20
        assert days_left(ablage, days=30, now=JETZT + timedelta(days=99)) == 0

    def test_ohne_testzeitraum_keine_restzeit(self, ablage: RegistrationStore) -> None:
        assert days_left(ablage, days=30, now=JETZT) is None


class TestModusVerhalten:
    """Die drei Modi unterscheiden sich darin, WIE OFT gefragt wird."""

    def test_frei_fragt_genau_einmal(self, ablage: RegistrationStore) -> None:
        """Beim ersten Start ein Hinweis, danach Ruhe.

        Eine zweite Nachfrage waere keine Erinnerung mehr, sondern
        Belaestigung - und der schnellste Weg, dass jemand die Anwendung
        wieder loescht.
        """
        _, oeffentlich = create_keypair()
        assert check(ablage, oeffentlich, mode=Mode.FREE, now=JETZT) is Outcome.REMIND
        for _ in range(5):
            assert check(ablage, oeffentlich, mode=Mode.FREE, now=JETZT) is Outcome.CONTINUE

    def test_testzeitraum_fragt_bei_jedem_start(self, ablage: RegistrationStore) -> None:
        """Wegklickbar, aber jedes Mal da - solange die Frist laeuft."""
        _, oeffentlich = create_keypair()
        for tag in range(5):
            zeit = JETZT + timedelta(days=tag)
            assert check(ablage, oeffentlich, mode=Mode.TRIAL, now=zeit) is Outcome.REMIND

    def test_pflicht_fragt_bei_jedem_start_und_laesst_nicht_durch(
        self, ablage: RegistrationStore
    ) -> None:
        _, oeffentlich = create_keypair()
        for _ in range(3):
            assert check(ablage, oeffentlich, mode=Mode.REQUIRED, now=JETZT) is Outcome.QUIT

    def test_nach_der_registrierung_fragt_keiner_mehr(
        self, ablage: RegistrationStore, schluessel: tuple[bytes, bytes]
    ) -> None:
        privat, oeffentlich = schluessel
        check(ablage, oeffentlich, mode=Mode.TRIAL, now=JETZT)
        stand = ablage.load()
        ablage.save(Registration(license=sign("michael@example.com", privat), trial=stand.trial))
        assert check(ablage, oeffentlich, mode=Mode.TRIAL, now=JETZT) is Outcome.CONTINUE
