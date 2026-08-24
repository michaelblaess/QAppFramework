"""QAppFramework - gemeinsame Bausteine fuer PySide6-Anwendungen.

Damit mehrere Desktop-Anwendungen gleich aussehen und sich gleich verhalten:
wer von einer zur naechsten wechselt, soll sich nicht umgewoehnen muessen.

Enthalten:

- about:         Info-Dialog mit Zitatpool
- absturz:       Fehlerdialog statt wortlosem Abbruch, geordnetes Strg+C
- zelle:         Zell-Delegate mit Innenabstand und Trefferhervorhebung
- einstellungen: Geruest fuer Einstellungsdialoge, Seiten Darstellung und Speicherort
- farbe:         Farbeingaben normalisieren
- theme:      Palette, Stylesheet, Fusion-Grundeinstellung, Erscheinungsbild
              (hell/dunkel/System), Akzentfarbe und Zoom als Zustand
- texte:      die wenigen zweisprachigen Woerter der Bibliothek
- icons:      Sinnbilder ueber QtAwesome, zur Laufzeit einfaerbbar
- disclaimer: bestaetigungspflichtiger Haftungshinweis beim ersten Start

Bewusst NICHT enthalten: alles, was nur eine Anwendung braucht. Ein Baustein
wandert erst hierher, wenn ihn die zweite Anwendung ebenfalls verwendet.
"""

from .about import AboutDialog, Zitat, lade_zitate
from .absturz import FehlerDialog, abbruch_abfangen, baue_bericht, einhaengen
from .disclaimer import DISCLAIMER_VERSION, LIABILITY, DisclaimerDialog, DisclaimerStore
from .einstellungen import BasisEinstellungenDialog, Darstellung
from .farbe import ist_hell, normalisiere
from .icons import GLYPHEN, lade_icon
from .texte import SPRACHEN, text
from .theme import (
    AKZENTE,
    DUNKEL,
    HELL,
    STANDARD_AKZENT,
    STANDARD_ZOOM,
    ZOOMSTUFEN,
    Akzent,
    Farben,
    Modus,
    akzent,
    akzent_namen,
    anwenden,
    baue_palette,
    baue_qss,
    farben,
    ist_dunkel,
    modus,
    naechster_zoom,
    setze_akzent,
    setze_modus,
    setze_zoom,
    skaliere,
    system_ist_dunkel,
    umgeschaltet,
    umschalten,
    zoom,
)
from .zelle import ZELLRAND_RECHTS, ZellDelegate

__version__ = "0.10.0"
__author__ = "Michael Blaess"

__all__ = [
    "AKZENTE",
    "AboutDialog",
    "Akzent",
    "BasisEinstellungenDialog",
    "DISCLAIMER_VERSION",
    "DUNKEL",
    "Darstellung",
    "DisclaimerDialog",
    "DisclaimerStore",
    "Farben",
    "FehlerDialog",
    "GLYPHEN",
    "HELL",
    "LIABILITY",
    "Modus",
    "SPRACHEN",
    "STANDARD_AKZENT",
    "STANDARD_ZOOM",
    "ZELLRAND_RECHTS",
    "ZOOMSTUFEN",
    "ZellDelegate",
    "Zitat",
    "__author__",
    "__version__",
    "abbruch_abfangen",
    "akzent",
    "akzent_namen",
    "anwenden",
    "baue_bericht",
    "baue_palette",
    "baue_qss",
    "einhaengen",
    "farben",
    "ist_dunkel",
    "ist_hell",
    "lade_icon",
    "lade_zitate",
    "modus",
    "naechster_zoom",
    "normalisiere",
    "setze_akzent",
    "setze_modus",
    "setze_zoom",
    "skaliere",
    "system_ist_dunkel",
    "text",
    "umgeschaltet",
    "umschalten",
    "zoom",
]
