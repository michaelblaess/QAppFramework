"""Registrierung und Testzeitraum - der Kern, ohne Oberflaeche.

Das Modell: wer die Anwendung selbst aus dem Quelltext baut, darf sie
uneingeschraenkt benutzen (so steht es im Additional Use Grant der Lizenz). Die
fertigen Programmpakete sind kostenpflichtig und verlangen einen Schluessel.

Geprueft wird mit einer **Signatur**, nicht mit einer berechneten Nummer. Der
private Schluessel bleibt beim Herausgeber, die Anwendung traegt nur den
oeffentlichen. Damit ist ein Schluesselgenerator nicht schwer, sondern
unmoeglich - angreifen laesst sich nur noch die Pruefung selbst, und das ist
Patchen des Kompilats, nicht Nachbauen.

Bewusst NICHT enthalten: Aufrufe nach Hause, Hardware-Kennungen, ein zweiter
Ablageort in der Registry. Die Registry ist ausdruecklich tabu, und alles
Weitere kostet mehr Zeit, als es je einbringt.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

logger = logging.getLogger(__name__)


class RegistrationMode(Enum):
    """Wie streng die Anwendung die Registrierung nimmt."""

    REQUIRED = auto()
    """Ohne Schluessel geht es nicht weiter."""

    TRIAL = auto()
    """Ohne Schluessel nur fuer eine begrenzte Zeit."""

    FREE = auto()
    """Ohne Schluessel dauerhaft nutzbar, die Registrierung ist erwuenscht."""


class RegistrationOutcome(Enum):
    """Was die Anwendung nach der Pruefung tun soll."""

    CONTINUE = auto()
    """Weiter, ohne Hinweis."""

    REMIND = auto()
    """Weiter, aber die Anwendung soll auf die Registrierung hinweisen."""

    QUIT = auto()
    """Nicht weiter - der Testzeitraum ist abgelaufen oder ein Schluessel fehlt."""


@dataclass(frozen=True)
class License:
    """Ein ausgestellter Schluessel."""

    email: str
    signature: bytes

    def as_text(self) -> str:
        """Die Lizenzdatei als Text, wie sie beim Anwender liegt."""
        return json.dumps(
            {"email": self.email, "signature": self.signature.hex()},
            indent=2,
            ensure_ascii=False,
        )

    @classmethod
    def from_text(cls, text: str) -> License | None:
        """Liest eine Lizenzdatei, oder None wenn sie unbrauchbar ist."""
        try:
            roh = json.loads(text)
            return cls(email=str(roh["email"]), signature=bytes.fromhex(str(roh["signature"])))
        except Exception:
            logger.warning("Lizenzdatei konnte nicht gelesen werden")
            return None


def normalize_email(email: str) -> str:
    """Die Form, ueber die signiert und geprueft wird.

    Ohne Normalisierung scheitert ein Schluessel an einem Leerzeichen oder
    einem grossen Anfangsbuchstaben, und niemand versteht warum.
    """
    return email.strip().casefold()


def create_keypair() -> tuple[bytes, bytes]:
    """Erzeugt ein neues Schluesselpaar.

    Returns:
        (privat, oeffentlich) als rohe Bytes. Der private Schluessel darf
        niemals in ein Repo oder in ein Programmpaket - geht er verloren, sind
        alle bisher ausgestellten Lizenzen wertlos.
    """
    privat = SigningKey.generate()
    return bytes(privat), bytes(privat.verify_key)


def sign(email: str, private_key: bytes) -> License:
    """Stellt einen Schluessel aus. Laeuft nur beim Herausgeber."""
    unterschrift = SigningKey(private_key).sign(normalize_email(email).encode()).signature
    return License(email=email.strip(), signature=unterschrift)


def verify(license_: License | None, public_key: bytes) -> bool:
    """Prueft einen Schluessel. Laeuft in der Anwendung."""
    if license_ is None:
        return False
    try:
        VerifyKey(public_key).verify(
            normalize_email(license_.email).encode(), license_.signature
        )
    except (BadSignatureError, ValueError, TypeError):
        return False
    return True


@dataclass(frozen=True)
class TrialState:
    """Was ueber den Testzeitraum bekannt ist.

    `latest_seen` ist der Riegel gegen die zurueckgestellte Uhr: es ist der
    hoechste je gesehene Zeitpunkt. Liegt die aktuelle Zeit davor, wurde die
    Uhr manipuliert - dann gilt der Testzeitraum als abgelaufen, nicht als
    verlaengert.

    `launches` zaehlt die Starts und laeuft damit voellig unabhaengig von jeder
    Uhr. Wer die Zeit anhaelt, laeuft in diese zweite Schranke.
    """

    first_seen: datetime
    latest_seen: datetime
    launches: int = 0

    def days_used(self, now: datetime) -> int:
        """Vergangene Tage seit dem ersten Start."""
        return max(0, (max(now, self.latest_seen) - self.first_seen).days)

    def clock_turned_back(self, now: datetime) -> bool:
        """Ob die Uhr hinter den hoechsten bekannten Stand zurueckgesetzt wurde.

        Eine Minute Spielraum, damit Zeitzonen- und Synchronisierungsspruenge
        keinen ehrlichen Anwender aussperren.
        """
        return (self.latest_seen - now).total_seconds() > 60


def start_trial(now: datetime) -> TrialState:
    """Der Zustand beim allerersten Start."""
    return TrialState(first_seen=now, latest_seen=now, launches=1)


def record_launch(state: TrialState, now: datetime) -> TrialState:
    """Schreibt einen Start fort, ohne den hoechsten Zeitpunkt je zu senken."""
    return replace(
        state,
        latest_seen=max(state.latest_seen, now),
        launches=state.launches + 1,
    )


def trial_expired(state: TrialState, now: datetime, *, days: int, max_launches: int) -> bool:
    """Ob der Testzeitraum vorbei ist.

    Drei Wege fuehren dorthin: die Tage sind um, die Zahl der Starts ist
    erreicht, oder die Uhr wurde zurueckgestellt.
    """
    if state.clock_turned_back(now):
        logger.info("Testzeitraum: die Systemzeit liegt vor dem letzten bekannten Start")
        return True
    return state.days_used(now) >= days or state.launches > max_launches


@dataclass(frozen=True)
class Registration:
    """Alles, was ueber den Anwender gespeichert wird."""

    license: License | None = None
    trial: TrialState | None = None


class RegistrationStore:
    """Legt die Registrierung in einer JSON-Datei ab.

    Anders als beim Einstellungsdialog kennt die Bibliothek die Ablage hier
    absichtlich: E-Mail, Schluessel und Testzeitraum sind ueberall derselbe
    Satz, und jede Anwendung wuerde ihn sonst anders rechnen.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        """Wo die Datei liegt - fuer die Anzeige im Einstellungsdialog."""
        return self._path

    def load(self) -> Registration:
        """Liest die Ablage. Fehlt sie oder ist sie kaputt, faengt alles bei null an."""
        if not self._path.is_file():
            return Registration()
        try:
            roh = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Registrierung konnte nicht gelesen werden - beginnt neu")
            return Registration()
        lizenz = None
        if isinstance(roh.get("license"), dict):
            lizenz = License.from_text(json.dumps(roh["license"]))
        versuch = None
        try:
            if isinstance(roh.get("trial"), dict):
                t = roh["trial"]
                versuch = TrialState(
                    first_seen=datetime.fromisoformat(t["first_seen"]),
                    latest_seen=datetime.fromisoformat(t["latest_seen"]),
                    launches=int(t.get("launches", 0)),
                )
        except Exception:
            logger.warning("Testzeitraum konnte nicht gelesen werden")
        return Registration(license=lizenz, trial=versuch)

    def save(self, registration: Registration) -> None:
        """Schreibt die Ablage. Ein Fehler darf den Start nicht verhindern."""
        daten: dict[str, object] = {}
        if registration.license is not None:
            daten["license"] = {
                "email": registration.license.email,
                "signature": registration.license.signature.hex(),
            }
        if registration.trial is not None:
            daten["trial"] = {
                "first_seen": registration.trial.first_seen.isoformat(),
                "latest_seen": registration.trial.latest_seen.isoformat(),
                "launches": registration.trial.launches,
            }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n"
            )
        except OSError:
            logger.exception("Registrierung konnte nicht gespeichert werden")


def check_registration(
    store: RegistrationStore,
    public_key: bytes,
    *,
    mode: RegistrationMode,
    days: int = 30,
    max_launches: int = 60,
    enforced: bool = True,
    now: datetime | None = None,
) -> RegistrationOutcome:
    """Prueft die Registrierung und sagt, wie es weitergeht.

    Args:
        store:
            Die Ablage.
        public_key:
            Der oeffentliche Schluessel des Herausgebers.
        mode:
            Wie streng die Anwendung die Registrierung nimmt.
        days:
            Laenge des Testzeitraums in Tagen.
        max_launches:
            Zweite Schranke, unabhaengig von der Uhr.
        enforced:
            **Nur die offiziellen Programmpakete setzen das.** Wer selbst aus
            dem Quelltext baut, darf die Anwendung laut Lizenz uneingeschraenkt
            nutzen - eine Pruefung, die ihn aussperrt, widerspraeche der eigenen
            Lizenz. Ohne dieses Kennzeichen ist das Ergebnis immer CONTINUE.
        now:
            Fuer Tests. Sonst die aktuelle Zeit.

    Returns:
        CONTINUE, REMIND oder QUIT.
    """
    if not enforced:
        return RegistrationOutcome.CONTINUE

    jetzt = now or datetime.now(UTC)
    stand = store.load()

    if verify(stand.license, public_key):
        return RegistrationOutcome.CONTINUE

    if mode is RegistrationMode.REQUIRED:
        return RegistrationOutcome.QUIT

    if mode is RegistrationMode.FREE:
        return RegistrationOutcome.REMIND

    versuch = record_launch(stand.trial, jetzt) if stand.trial else start_trial(jetzt)
    store.save(replace(stand, trial=versuch))
    if trial_expired(versuch, jetzt, days=days, max_launches=max_launches):
        return RegistrationOutcome.QUIT
    return RegistrationOutcome.REMIND


def days_left(
    store: RegistrationStore, *, days: int = 30, now: datetime | None = None
) -> int | None:
    """Verbleibende Tage im Testzeitraum, oder None wenn keiner laeuft.

    Fuer den Hinweis, den die Anwendung bei REMIND anzeigt.
    """
    stand = store.load()
    if stand.trial is None:
        return None
    return max(0, days - stand.trial.days_used(now or datetime.now(UTC)))
