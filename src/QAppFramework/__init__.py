"""QAppFramework - gemeinsame Bausteine fuer PySide6-Anwendungen.

Damit mehrere Desktop-Anwendungen gleich aussehen und sich gleich verhalten:
wer von einer zur naechsten wechselt, soll sich nicht umgewoehnen muessen.

Enthalten:

- about:         Info-Dialog mit Zitatpool
- absturz:       Fehlerdialog statt wortlosem Abbruch, geordnetes Strg+C
- registration:  Schluessel pruefen und Testzeitraum rechnen, ohne Oberflaeche
- zelle:         Zell-Delegate mit Innenabstand und Trefferhervorhebung
- einstellungen: Geruest fuer Einstellungsdialoge, Seiten Appearance und Speicherort
- farbe:         Farbeingaben normalisieren
- theme:      Palette, Stylesheet, Fusion-Grundeinstellung, Erscheinungsbild
              (hell/dunkel/System), Akzentfarbe und Zoom als Zustand
- texte:      die wenigen zweisprachigen Woerter der Bibliothek
- icons:      Sinnbilder ueber QtAwesome, zur Laufzeit einfaerbbar
- disclaimer: bestaetigungspflichtiger Haftungshinweis beim ersten Start

Bewusst NICHT enthalten: alles, was nur eine Anwendung braucht. Ein Baustein
wandert erst hierher, wenn ihn die zweite Anwendung ebenfalls verwendet.
"""

from .about import AboutDialog, Quote, load_quotes
from .cell import CELL_PADDING_RIGHT, CellDelegate
from .color import is_light, normalize
from .crash import ErrorDialog, build_report, install_error_handler, install_interrupt_handler
from .disclaimer import DISCLAIMER_VERSION, LIABILITY, DisclaimerDialog, DisclaimerStore
from .icons import GLYPHS, load_icon
from .registration import (
    License,
    Registration,
    RegistrationMode,
    RegistrationOutcome,
    RegistrationStore,
    check_registration,
    create_keypair,
    days_left,
    sign,
    verify,
)
from .settings import Appearance, SettingsDialogBase
from .texts import LANGUAGES, text
from .theme import (
    ACCENTS,
    DARK,
    DEFAULT_ACCENT,
    DEFAULT_ZOOM,
    LIGHT,
    ZOOM_LEVELS,
    Accent,
    Colors,
    Mode,
    accent,
    accent_names,
    apply_theme,
    build_palette,
    build_stylesheet,
    colors,
    is_dark,
    mode,
    next_zoom,
    scale,
    set_accent,
    set_mode,
    set_zoom,
    system_is_dark,
    toggle,
    toggled,
    zoom,
)

__version__ = "0.11.0"
__author__ = "Michael Blaess"

__all__ = [
    "verify",
    "sign",
    "days_left",
    "create_keypair",
    "check_registration",
    "RegistrationStore",
    "RegistrationOutcome",
    "RegistrationMode",
    "Registration",
    "License",
    "ACCENTS",
    "AboutDialog",
    "Accent",
    "SettingsDialogBase",
    "DISCLAIMER_VERSION",
    "DARK",
    "Appearance",
    "DisclaimerDialog",
    "DisclaimerStore",
    "Colors",
    "ErrorDialog",
    "GLYPHS",
    "LIGHT",
    "LIABILITY",
    "Mode",
    "LANGUAGES",
    "DEFAULT_ACCENT",
    "DEFAULT_ZOOM",
    "CELL_PADDING_RIGHT",
    "ZOOM_LEVELS",
    "CellDelegate",
    "Quote",
    "__author__",
    "__version__",
    "install_interrupt_handler",
    "accent",
    "accent_names",
    "apply_theme",
    "build_report",
    "build_palette",
    "build_stylesheet",
    "install_error_handler",
    "colors",
    "is_dark",
    "is_light",
    "load_icon",
    "load_quotes",
    "mode",
    "next_zoom",
    "normalize",
    "set_accent",
    "set_mode",
    "set_zoom",
    "scale",
    "system_is_dark",
    "text",
    "toggled",
    "toggle",
    "zoom",
]
