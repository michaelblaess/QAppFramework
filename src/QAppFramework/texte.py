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
