"""QAppFramework - gemeinsame Bausteine fuer PySide6-Anwendungen.

Damit mehrere Desktop-Anwendungen gleich aussehen und sich gleich verhalten:
wer von einer zur naechsten wechselt, soll sich nicht umgewoehnen muessen.

Enthalten:

- about:         Info-Dialog mit Zitatpool
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
    system_ist_dunkel,
    umgeschaltet,
    umschalten,
    zoom,
)

__version__ = "0.5.0"
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
    "GLYPHEN",
    "HELL",
    "LIABILITY",
    "Modus",
    "SPRACHEN",
    "STANDARD_AKZENT",
    "STANDARD_ZOOM",
    "ZOOMSTUFEN",
    "Zitat",
    "__author__",
    "__version__",
    "akzent",
    "akzent_namen",
    "anwenden",
    "baue_palette",
    "baue_qss",
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
    "system_ist_dunkel",
    "text",
    "umgeschaltet",
    "umschalten",
    "zoom",
]
