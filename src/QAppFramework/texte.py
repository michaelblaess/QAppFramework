"""Zweisprachige Texte der Bibliothek.

Die Dialoge der Bibliothek erscheinen in den Anwendungen, also brauchen sie
deren Sprache. Jeder nimmt dafuer ein `sprache`-Argument, wie die Bausteine in
textual-widgets - Vorgabe ist Deutsch, weil die Anwendungen deutsch starten.

Ein eigenes Uebersetzungssystem waere hier zu viel: es geht um wenige Woerter,
die sich selten aendern. Sie stehen deshalb als Abbildung im Code und nicht in
einer Datei, die mitgeliefert und gefunden werden muesste.
"""

from __future__ import annotations

SPRACHEN = ("de", "en")
STANDARDSPRACHE = "de"

# Schluessel -> Sprache -> Text. Flach gehalten: eine Ebene reicht, und ein
# fehlender Schluessel faellt beim Nachschlagen sofort auf.
TEXTE: dict[str, dict[str, str]] = {
    "akzent.orange": {"de": "Orange", "en": "Orange"},
    "akzent.blau": {"de": "Blau", "en": "Blue"},
    "akzent.gruen": {"de": "Grün", "en": "Green"},
    "akzent.tuerkis": {"de": "Türkis", "en": "Turquoise"},
    "akzent.violett": {"de": "Violett", "en": "Violet"},
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
    "modus.system": {"de": "Wie das Betriebssystem", "en": "Match the system"},
    "modus.dark": {"de": "Dunkel", "en": "Dark"},
    "modus.light": {"de": "Hell", "en": "Light"},
}


def pruefe_sprache(sprache: str) -> str:
    """Faellt auf die Standardsprache zurueck, statt an einem Tippfehler zu scheitern."""
    return sprache if sprache in SPRACHEN else STANDARDSPRACHE


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
