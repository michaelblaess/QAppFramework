"""QAppFramework - gemeinsame Bausteine fuer PySide6-Anwendungen.

Damit mehrere Desktop-Anwendungen gleich aussehen und sich gleich verhalten:
wer von einer zur naechsten wechselt, soll sich nicht umgewoehnen muessen.

Enthalten:

- theme:      Palette, Stylesheet, Fusion-Grundeinstellung
- icons:      Sinnbilder ueber QtAwesome, zur Laufzeit einfaerbbar
- disclaimer: bestaetigungspflichtiger Haftungshinweis beim ersten Start

Bewusst NICHT enthalten: alles, was nur eine Anwendung braucht. Ein Baustein
wandert erst hierher, wenn ihn die zweite Anwendung ebenfalls verwendet.
"""

from .disclaimer import DISCLAIMER_VERSION, LIABILITY, DisclaimerDialog, DisclaimerStore
from .icons import GLYPHEN, lade_icon
from .theme import DUNKEL, HELL, Farben, anwenden, baue_palette, baue_qss, farben, ist_dunkel

__version__ = "0.1.0"
__author__ = "Michael Blaess"

__all__ = [
    "DISCLAIMER_VERSION",
    "DUNKEL",
    "GLYPHEN",
    "HELL",
    "LIABILITY",
    "DisclaimerDialog",
    "DisclaimerStore",
    "Farben",
    "__author__",
    "__version__",
    "anwenden",
    "baue_palette",
    "baue_qss",
    "farben",
    "ist_dunkel",
    "lade_icon",
]
