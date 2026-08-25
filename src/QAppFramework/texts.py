"""Zweisprachige Texte der Bibliothek.

Die Dialoge der Bibliothek erscheinen in den Anwendungen, also brauchen sie
deren Sprache. Jeder nimmt dafuer ein `sprache`-Argument, wie die Bausteine in
textual-widgets - Vorgabe ist Deutsch, weil die Anwendungen deutsch starten.

Ein eigenes Uebersetzungssystem waere hier zu viel: es geht um wenige Woerter,
die sich selten aendern. Sie stehen deshalb als Abbildung im Code und nicht in
einer Datei, die mitgeliefert und gefunden werden muesste.
"""

from __future__ import annotations

LANGUAGES = ("de", "en")
STANDARDSPRACHE = "de"

# Schluessel -> Sprache -> Text. Flach gehalten: eine Ebene reicht, und ein
# fehlender Schluessel faellt beim Nachschlagen sofort auf.
TEXTE: dict[str, dict[str, str]] = {
    "accent.orange": {"de": "Orange", "en": "Orange"},
    "accent.blau": {"de": "Blau", "en": "Blue"},
    "accent.gruen": {"de": "Grün", "en": "Green"},
    "accent.tuerkis": {"de": "Türkis", "en": "Turquoise"},
    "accent.violett": {"de": "Violett", "en": "Violet"},
    "about.titel": {"de": "Über", "en": "About"},
    "common.schliessen": {"de": "Schließen", "en": "Close"},
    "absturz.titel": {"de": "Ein Fehler ist aufgetreten", "en": "Something went wrong"},
    "absturz.erklaerung": {
        "de": (
            "Entschuldige bitte. Der Bericht unten hilft bei der Ursachensuche - Du kannst ihn "
            "kopieren und weitergeben. Weiterarbeiten ist möglich, kann aber zu Folgefehlern führen."
        ),
        "en": (
            "Sorry about that. The report below helps to find the cause - you can copy it and "
            "pass it on. Carrying on is possible but may lead to follow-up errors."
        ),
    },
    "absturz.kopieren": {"de": "Bericht kopieren", "en": "Copy report"},
    "absturz.beenden": {"de": "Beenden", "en": "Quit"},
    "absturz.weiter": {"de": "Weiterarbeiten", "en": "Carry on"},
    "about.registrieren": {"de": "Registrieren ...", "en": "Register ..."},
    "about.registriert": {
        "de": "Registriert für {mail}",
        "en": "Registered to {mail}",
    },
    "about.nicht_registriert": {
        "de": "Nicht registriert",
        "en": "Not registered",
    },
    "about.testzeit": {
        "de": "Testzeitraum - noch {tage} Tage",
        "en": "Trial period - {tage} days left",
    },
    "about.testzeit_abgelaufen": {
        "de": "Testzeitraum abgelaufen",
        "en": "Trial period has ended",
    },
    "registrierung.titel": {"de": "Registrierung", "en": "Registration"},
    "registrierung.freiwillig": {
        "de": "Diese Anwendung lässt sich uneingeschränkt nutzen. Wer sich registriert, "
              "bekommt zusätzliche Funktionen und wird über neue Versionen informiert. "
              "Diese Frage erscheint nur dieses eine Mal.",
        "en": "This application is fully usable as is. Registering unlocks additional "
              "features and keeps you informed about new versions. You will only be asked "
              "this once.",
    },
    "registrierung.testzeit": {
        "de": "Der Testzeitraum läuft noch {tage} Tage. Danach wird ein Schlüssel benötigt.",
        "en": "Your trial period runs for another {tage} days. After that a key is required.",
    },
    "registrierung.abgelaufen": {
        "de": "Der Testzeitraum ist abgelaufen. Zum Weiterarbeiten wird ein Schlüssel benötigt.",
        "en": "Your trial period has ended. A key is required to continue.",
    },
    "registrierung.pflicht": {
        "de": "Zum Verwenden dieser Anwendung wird ein Schlüssel benötigt.",
        "en": "A key is required to use this application.",
    },
    "registrierung.datei_platzhalter": {
        "de": "Noch keine Lizenzdatei ausgewählt",
        "en": "No licence file selected yet",
    },
    "registrierung.datei_waehlen": {"de": "Datei wählen ...", "en": "Choose file ..."},
    "registrierung.oder_einfuegen": {
        "de": "Oder den Inhalt der Lizenzdatei hier einfügen:",
        "en": "Or paste the contents of your licence file here:",
    },
    "registrierung.gueltig": {
        "de": "Schlüssel gültig, ausgestellt für {mail}",
        "en": "Key valid, issued to {mail}",
    },
    "registrierung.ungueltig": {
        "de": "Dieser Schlüssel ist nicht gültig. Bitte prüfe, ob der Inhalt vollständig ist.",
        "en": "This key is not valid. Please check that the contents are complete.",
    },
    "registrierung.datei_fehler": {
        "de": "Die Datei konnte nicht gelesen werden.",
        "en": "The file could not be read.",
    },
    "registrierung.uebernehmen": {"de": "Übernehmen", "en": "Apply"},
    "registrierung.spaeter": {"de": "Später", "en": "Later"},
    "registrierung.beenden": {"de": "Beenden", "en": "Quit"},
    "einstellungen.titel": {"de": "Einstellungen", "en": "Settings"},
    "einstellungen.darstellung": {"de": "Darstellung", "en": "Appearance"},
    "einstellungen.erscheinungsbild": {"de": "Erscheinungsbild", "en": "Theme"},
    "einstellungen.akzentfarbe": {"de": "Akzentfarbe", "en": "Accent colour"},
    "einstellungen.zoom": {"de": "Zoom", "en": "Zoom"},
    "einstellungen.sofort": {
        "de": "Ein Wechsel wirkt sofort, ohne Neustart.",
        "en": "Changes take effect at once, no restart needed.",
    },
    "einstellungen.speicherort": {"de": "Speicherort", "en": "Storage"},
    "einstellungen.oeffnen": {"de": "Öffnen", "en": "Open"},
    "einstellungen.ortehinweis": {
        "de": "Ein Klick öffnet den Ordner. Die Anwendung überschreibt diese Dateien beim Speichern.",
        "en": "A click opens the folder. The application overwrites these files when saving.",
    },
    "einstellungen.speichern": {"de": "Speichern", "en": "Save"},
    "einstellungen.abbrechen": {"de": "Abbrechen", "en": "Cancel"},
    "mode.system": {"de": "Wie das Betriebssystem", "en": "Match the system"},
    "mode.dark": {"de": "Dunkel", "en": "Dark"},
    "mode.light": {"de": "Hell", "en": "Light"},
}


def pruefe_sprache(sprache: str) -> str:
    """Faellt auf die Standardsprache zurueck, statt an einem Tippfehler zu scheitern."""
    return sprache if sprache in LANGUAGES else STANDARDSPRACHE


def text(schluessel: str, sprache: str = STANDARDSPRACHE) -> str:
    """Liefert den Text zum Schluessel.

    Args:
        schluessel:
            Der Schluessel aus TEXTE.
        sprache:
            'de' oder 'en'. Unbekannte Angaben ergeben Deutsch.

    Returns:
        Der uebersetzte Text. Ist der Schluessel unbekannt, der Schluessel
        selbst - so steht im Fenster etwas Nachvollziehbares statt einer
        Ausnahme mitten im Aufbau.
    """
    eintrag = TEXTE.get(schluessel)
    return eintrag[pruefe_sprache(sprache)] if eintrag else schluessel
