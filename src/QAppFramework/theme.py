"""Erscheinungsbild: Fusion mit QPalette, dazu ein duennes Stylesheet.

DIES IST DIE QUELLE fuer alle PySide6-Anwendungen. Wer von einer Anwendung zur
naechsten wechselt, soll sich nicht umgewoehnen muessen - deshalb wird das hier
NICHT je Anwendung kopiert und abgewandelt.

Die Werte stammen urspruenglich aus jira-timesheet-qt 0.7.1 und sind von dort
uebernommen. Aendert sich hier etwas, gilt es fuer alle.

Der Ansatz bleibt zurueckhaltend: Fusion zeichnet die Bedienelemente, die
Palette faerbt sie, das Stylesheet regelt nur Struktur und Schrift. Bewusst
konservativ - die Anwendungen sollen ohne Einarbeitung bedienbar sein.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette

from .texte import text as _text


@dataclass(frozen=True)
class Farben:
    """Feldnamen wie die Palette in jira-timesheet-qt."""

    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    bg_elevated: str
    border: str
    border_hover: str
    text_primary: str
    text_secondary: str
    text_tertiary: str
    accent: str
    accent_hover: str
    accent_subtle: str
    green: str
    orange: str
    red: str
    purple: str


# Werte woertlich aus jira-timesheet-qt. Reihenfolge der Flaechen nach
# Helligkeit: bg_primary (Fenster) - bg_secondary (Panels) - bg_tertiary
# (Tabelle) - bg_elevated (Schaltflaechen).
DUNKEL = Farben(
    bg_primary="#1f2226",
    bg_secondary="#23262b",
    bg_tertiary="#26292e",
    bg_elevated="#2f333a",
    border="#3a3f47",
    border_hover="#4a505a",
    text_primary="#e2e5ea",
    text_secondary="#9aa2ad",
    text_tertiary="#6f7680",
    accent="#ff922b",
    accent_hover="#ffa94d",
    accent_subtle="rgba(255, 146, 43, 0.20)",
    green="#5a9e83",
    orange="#c39a52",
    red="#c96f6f",
    purple="#8f83b0",
)

HELL = Farben(
    bg_primary="#f4f5f7",
    bg_secondary="#f0f1f4",
    bg_tertiary="#ffffff",
    bg_elevated="#eceef1",
    border="#d3d7dd",
    border_hover="#b9bec6",
    text_primary="#1c1f24",
    text_secondary="#5f6773",
    text_tertiary="#8b929e",
    accent="#e8590c",
    accent_hover="#fd7e14",
    accent_subtle="rgba(232, 89, 12, 0.14)",
    green="#2f8f6b",
    orange="#b0791f",
    red="#b64a4a",
    purple="#6f5fa0",
)

RADIUS_SM = 4
RADIUS_MD = 6

# Qt liefert fuer Werkzeugleisten von sich aus 24 Pixel. jira-timesheet-qt setzt
# nichts anderes, also wird hier ebenfalls nichts gesetzt. Der Wert steht nur
# als Erwartung fuer den Test, nicht als Vorgabe an die Leiste.
TOOLBAR_ICON_SIZE = 24


class Modus(StrEnum):
    """Erscheinungsbild. Die Werte landen in den Einstellungsdateien.

    Sie stimmen mit denen in jira-timesheet-qt ueberein - eine vorhandene
    Einstellung soll nach der Umstellung weiter gelten.
    """

    SYSTEM = "system"
    DUNKEL = "dark"
    HELL = "light"


@dataclass(frozen=True)
class Akzent:
    """Ein Satz Akzentfarben: Grundton, Hover, durchscheinende Flaeche."""

    accent: str
    accent_hover: str
    accent_subtle: str


# Je Name ein Paar (dunkel, hell). Getrennt, weil ein Ton, der auf dunklem
# Grund traegt, auf hellem zu blass wird - und umgekehrt. Die Schluessel
# stehen in Einstellungsdateien und bleiben deshalb unveraendert, der
# Anzeigename kommt aus texte.py.
AKZENTE: dict[str, tuple[Akzent, Akzent]] = {
    "orange": (
        Akzent("#ff922b", "#ffa94d", "rgba(255, 146, 43, 0.20)"),
        Akzent("#e8590c", "#fd7e14", "rgba(232, 89, 12, 0.14)"),
    ),
    "blau": (
        Akzent("#4dabf7", "#74c0fc", "rgba(77, 171, 247, 0.20)"),
        Akzent("#1c7ed6", "#1971c2", "rgba(28, 126, 214, 0.14)"),
    ),
    "gruen": (
        Akzent("#51cf66", "#69db7c", "rgba(81, 207, 102, 0.20)"),
        Akzent("#2f9e44", "#37b24d", "rgba(47, 158, 68, 0.14)"),
    ),
    "tuerkis": (
        Akzent("#22b8cf", "#3bc9db", "rgba(34, 184, 207, 0.20)"),
        Akzent("#0c8599", "#1098ad", "rgba(12, 133, 153, 0.14)"),
    ),
    "violett": (
        Akzent("#b197fc", "#d0bfff", "rgba(177, 151, 252, 0.20)"),
        Akzent("#7048e8", "#7950f2", "rgba(112, 72, 232, 0.14)"),
    ),
}

STANDARD_AKZENT = "orange"

# Zoomstufen der Oberflaeche in Prozent.
ZOOMSTUFEN: tuple[int, ...] = (80, 90, 100, 110, 125, 150, 175, 200)
STANDARD_ZOOM = 100

# Erscheinungsbild, Akzent und Zoom gelten fuer die ganze Anwendung - genau wie
# das Stylesheet, an dem sie haengen. Deshalb Modulzustand und kein Wert, der
# durch jeden Aufruf gereicht werden muesste.
_modus: Modus = Modus.SYSTEM
_akzent: str = STANDARD_AKZENT
_zoom: int = STANDARD_ZOOM


def setze_modus(wert: Modus | str) -> None:
    """Setzt das Erscheinungsbild. Unbekannte Angaben ergeben SYSTEM."""
    global _modus
    try:
        _modus = Modus(wert)
    except ValueError:
        _modus = Modus.SYSTEM


def modus() -> Modus:
    """Das eingestellte Erscheinungsbild - SYSTEM, wenn es dem System folgt."""
    return _modus


def setze_akzent(name: str) -> None:
    """Setzt die Akzentfarbe. Unbekannte Namen ergeben den Standard."""
    global _akzent
    _akzent = name if name in AKZENTE else STANDARD_AKZENT


def akzent() -> str:
    """Name der aktiven Akzentfarbe."""
    return _akzent


def akzent_namen(sprache: str = "de") -> dict[str, str]:
    """Die waehlbaren Akzentfarben als Schluessel und Anzeigename."""
    return {name: _text(f"akzent.{name}", sprache) for name in AKZENTE}


def setze_zoom(prozent: int) -> None:
    """Setzt den Zoom der Oberflaeche, begrenzt auf die vorhandenen Stufen."""
    global _zoom
    _zoom = min(ZOOMSTUFEN[-1], max(ZOOMSTUFEN[0], int(prozent)))


def zoom() -> int:
    """Der aktive Zoom in Prozent."""
    return _zoom


def naechster_zoom(richtung: int) -> int:
    """Die naechste Zoomstufe hoch (1) oder runter (-1), ohne die Enden zu verlassen."""
    try:
        i = ZOOMSTUFEN.index(_zoom)
    except ValueError:
        i = ZOOMSTUFEN.index(STANDARD_ZOOM)
    return ZOOMSTUFEN[max(0, min(len(ZOOMSTUFEN) - 1, i + richtung))]


def umgeschaltet() -> Modus:
    """Das jeweils andere Erscheinungsbild - fuer den Umschalter der Werkzeugleiste.

    Aus SYSTEM wird das Gegenteil dessen, was gerade zu sehen ist. Sonst waere
    der erste Druck auf den Umschalter wirkungslos, wenn das System ohnehin
    schon dunkel ist.
    """
    return Modus.HELL if ist_dunkel() else Modus.DUNKEL


def system_ist_dunkel() -> bool:
    """Fragt das Farbschema des Systems ab (Qt 6.5 und neuer)."""
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return True


def ist_dunkel() -> bool:
    """Ob gerade dunkel dargestellt wird.

    Folgt dem eingestellten Erscheinungsbild. Nur bei SYSTEM wird das
    Betriebssystem gefragt - vorher tat das diese Funktion immer, und deshalb
    liess sich nichts umschalten.
    """
    if _modus is Modus.DUNKEL:
        return True
    if _modus is Modus.HELL:
        return False
    return system_ist_dunkel()


def farben(dunkel: bool | None = None) -> Farben:
    """Die Farbwerte des aktuellen Erscheinungsbilds, mit der aktiven Akzentfarbe.

    Args:
        dunkel:
            Erzwingt hell oder dunkel. Ohne Angabe gilt das eingestellte
            Erscheinungsbild.

    Returns:
        Die Farben. Die drei Akzentwerte stammen aus der gewaehlten
        Akzentfarbe, alles uebrige aus der Grundpalette.
    """
    ist_dunkles_bild = ist_dunkel() if dunkel is None else dunkel
    grund = DUNKEL if ist_dunkles_bild else HELL
    ton = AKZENTE.get(_akzent, AKZENTE[STANDARD_AKZENT])[0 if ist_dunkles_bild else 1]
    return replace(
        grund,
        accent=ton.accent,
        accent_hover=ton.accent_hover,
        accent_subtle=ton.accent_subtle,
    )


def baue_palette(p: Farben) -> QPalette:
    """Faerbt die nativen Bedienelemente.

    Fusion zeichnet Pfeile, Rahmen, Bildlaufleisten und den Kalender selbst -
    diese Teile hoeren auf die Palette, nicht auf das Stylesheet.
    """
    qp = QPalette()
    qp.setColor(QPalette.ColorRole.Window, QColor(p.bg_primary))
    qp.setColor(QPalette.ColorRole.WindowText, QColor(p.text_primary))
    qp.setColor(QPalette.ColorRole.Base, QColor(p.bg_tertiary))
    qp.setColor(QPalette.ColorRole.AlternateBase, QColor(p.bg_secondary))
    qp.setColor(QPalette.ColorRole.ToolTipBase, QColor(p.bg_elevated))
    qp.setColor(QPalette.ColorRole.ToolTipText, QColor(p.text_primary))
    qp.setColor(QPalette.ColorRole.Text, QColor(p.text_primary))
    qp.setColor(QPalette.ColorRole.Button, QColor(p.bg_elevated))
    qp.setColor(QPalette.ColorRole.ButtonText, QColor(p.text_primary))
    qp.setColor(QPalette.ColorRole.Highlight, QColor(p.accent))
    qp.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    qp.setColor(QPalette.ColorRole.PlaceholderText, QColor(p.text_tertiary))
    qp.setColor(QPalette.ColorRole.Link, QColor(p.accent))

    gruppe = QPalette.ColorGroup.Disabled
    qp.setColor(gruppe, QPalette.ColorRole.Text, QColor(p.text_tertiary))
    qp.setColor(gruppe, QPalette.ColorRole.ButtonText, QColor(p.text_tertiary))
    qp.setColor(gruppe, QPalette.ColorRole.WindowText, QColor(p.text_tertiary))
    return qp


def skaliere(qss: str) -> str:
    """Rechnet den aktiven Zoom in alle Schriftgroessen eines Stylesheets ein.

    Oeffentlich, weil eine Anwendung ihre eigenen Regeln an das Stylesheet der
    Bibliothek anhaengt. Ohne diesen Durchgang blieben genau die auf fester
    Groesse, waehrend der Rest mitwaechst.

    Ein Durchgang ueber das fertige Stylesheet statt einer Rechnung an jeder
    einzelnen Stelle. Die selbstgezeichneten Ansichten ziehen mit, ohne etwas
    zu tun: sie leiten ihre Schrift vom Widget-Font ab, und der kommt aus der
    globalen Regel, die hier mitskaliert wird.
    """
    if _zoom == STANDARD_ZOOM:
        return qss
    faktor = _zoom / 100.0
    return re.sub(
        r"font-size:\s*(\d+)px",
        lambda treffer: f"font-size: {max(1, round(int(treffer.group(1)) * faktor))}px",
        qss,
    )


def baue_qss(p: Farben) -> str:
    """Struktur und Schrift.

    Die Bloecke fuer Werkzeugleiste und Reiter sind woertlich aus
    jira-timesheet-qt uebernommen - Abstaende, Schriftstaerken und Farben
    inbegriffen. Wer hier etwas aendert, bricht die Wiedererkennung.
    """
    return skaliere(f"""
    QWidget {{ font-size: 13px; }}
    /* Die globale Flaechenregel wuerde sonst jedem Beschriftungsfeld einen
       eigenen Kasten geben. */
    QLabel {{ background: transparent; }}

    QMenuBar {{ background-color: {p.bg_secondary}; color: {p.text_primary};
                border-bottom: 1px solid {p.border}; }}
    QMenuBar::item {{ padding: 6px 12px; background: transparent; }}
    QMenuBar::item:selected {{ background-color: {p.bg_tertiary}; color: {p.text_primary}; }}
    /* Vollstaendiger Menue-Block: sobald app-weit ein Stylesheet gesetzt ist,
       zeichnet Qt die Menues selbst und laesst am gehoverten Eintrag das
       Sinnbild weg, wenn keine eigene Regel dafuer da ist. */
    QMenu {{ background-color: {p.bg_secondary}; color: {p.text_primary};
             border: 1px solid {p.border}; padding: 4px; }}
    QMenu::item {{ padding: 6px 28px 6px 28px; }}
    QMenu::item:selected {{ background-color: {p.accent_subtle}; color: {p.text_primary}; }}
    QMenu::item:disabled {{ color: {p.text_tertiary}; }}
    QMenu::separator {{ height: 1px; background-color: {p.border}; margin: 4px 8px; }}
    QMenu::icon {{ padding-left: 10px; }}

    QToolBar {{ background-color: {p.bg_secondary}; border-bottom: 1px solid {p.border};
                padding: 3px 6px; spacing: 2px; }}
    QToolBar::separator {{ background-color: {p.border}; width: 1px; margin: 4px 6px; }}
    QToolButton {{ background: transparent; border: none;
                   border-radius: {RADIUS_SM}px; padding: 5px; }}
    QToolButton:hover {{ background-color: {p.bg_tertiary}; }}
    QToolButton:pressed, QToolButton:checked {{ background-color: {p.accent_subtle}; }}

    #ViewTabs {{ background-color: {p.bg_secondary}; border-bottom: 1px solid {p.border}; }}
    #ViewTabs::tab {{ background: transparent; color: {p.text_secondary};
                      padding: 8px 18px; margin-right: 2px; border: none;
                      border-bottom: 2px solid transparent;
                      font-size: 13px; font-weight: 600; }}
    #ViewTabs::tab:hover {{ color: {p.text_primary}; }}
    #ViewTabs::tab:selected {{ color: {p.accent}; border-bottom: 2px solid {p.accent};
                               font-weight: 700; }}

    QStatusBar {{ background-color: {p.bg_secondary}; border-top: 1px solid {p.border}; }}
    QStatusBar::item {{ border: none; }}

    /* Ohne diese Regel zeichnet Qt den Hinweis in Systemfarben - auf einem
       dunklen Fenster ein heller Kasten. */
    QToolTip {{ background-color: {p.bg_elevated}; color: {p.text_primary};
                border: 1px solid {p.border}; padding: 6px 10px; }}
    /* Der Griff ist sonst kaum zu sehen, und der Trenner eines Hauptfensters
       gar nicht - beide muessen greifbar sein, nicht nur vorhanden. */
    QSplitter::handle {{ background-color: {p.border}; }}
    QMainWindow::separator {{ background-color: {p.text_tertiary}; width: 5px; height: 5px; }}
    /* Nur die Groesse. Eine ::item-Regel waere hier falsch: sobald es sie gibt,
       zeichnet das Stylesheet die Zellen und die Palette steuert sie nicht
       mehr - Wechselfarbe und Auswahl kaemen dann nicht mehr aus dem Thema. */
    QTableView {{ font-size: 14px; }}

    QDockWidget::title {{ background-color: {p.bg_secondary}; padding: 5px 8px;
                          border-top: 1px solid {p.border}; }}

    #Stat {{ border: 1px solid {p.border}; border-radius: {RADIUS_SM}px; padding: 2px 8px; }}
    #EmptyTitle {{ font-size: 19px; font-weight: bold; }}
    #EmptyText {{ color: {p.text_secondary}; }}
    #EmptyCard {{ background-color: {p.bg_secondary}; border: 1px solid {p.border};
                  border-radius: 12px; }}
    #Hint {{ color: {p.text_secondary}; }}
    /* Der Haftungshinweis wohnt in dieser Bibliothek - seine Regeln standen
       aber nur in jira-timesheet-qt. Derselbe Dialog sah deshalb in jeder
       Anwendung anders aus. */
    #DisclaimerTitle {{ font-size: 20px; font-weight: 700; color: {p.text_primary}; }}
    #DisclaimerSection {{ font-size: 13px; font-weight: 700; color: {p.text_primary};
                          padding-top: 4px; }}
    #DisclaimerText {{ color: {p.text_secondary}; font-size: 13px; }}
    #DisclaimerScroll {{ background-color: {p.bg_secondary}; border: 1px solid {p.border};
                         border-radius: {RADIUS_MD}px; padding: 14px; }}
    #DisclaimerScroll > QWidget > QWidget {{ background-color: {p.bg_secondary}; }}

    #SettingsNav {{ background-color: {p.bg_secondary}; border: none;
                    border-right: 1px solid {p.border}; padding: 14px 8px; outline: 0; }}
    #SettingsNav::item {{ padding: 9px 12px; border-radius: {RADIUS_SM}px;
                          color: {p.text_secondary}; font-weight: 600; }}
    #SettingsNav::item:hover {{ background-color: {p.bg_tertiary}; color: {p.text_primary}; }}
    #SettingsNav::item:selected {{ background-color: {p.accent_subtle}; color: {p.accent}; }}
    #SettingsHeading {{ font-size: 17px; font-weight: 700; color: {p.text_primary}; }}
    #SettingsLabel {{ color: {p.text_secondary}; font-weight: 600; }}
    #SettingsHint {{ color: {p.text_tertiary}; font-size: 12px; }}
    #SettingsPath {{ color: {p.text_secondary}; font-size: 12px;
                     font-family: Consolas, Menlo, "DejaVu Sans Mono"; }}

    #AboutBanner {{ background-color: {p.bg_secondary}; border-bottom: 1px solid {p.border}; }}
    #AboutName {{ font-size: 26px; font-weight: 800; color: {p.text_primary}; }}
    #AboutBannerText {{ color: {p.text_secondary}; font-size: 13px; }}
    /* Die Versionsmarke in Festbreitenschrift. Nur echte Familien nennen -
       ein Gattungsname wie "monospace" ist in Qt keine Familie und ergibt
       Kaestchen. */
    #AboutBadge {{ background-color: {p.accent}; color: #ffffff;
                   font-family: Consolas, Menlo, "DejaVu Sans Mono";
                   font-size: 12px; font-weight: 700;
                   padding: 3px 12px; border-radius: 9px; }}
    #AboutFacts {{ color: {p.text_tertiary}; font-size: 12px; }}
    #AboutQuote {{ color: {p.text_secondary}; font-size: 13px; font-style: italic; }}
    #AboutQuoteAuthor {{ color: {p.text_tertiary}; font-size: 12px; padding-top: 6px; }}
    #AboutLink {{ font-size: 12px; }}
    #AboutLink a {{ color: {p.accent_hover}; text-decoration: none; }}
    #Divider {{ background-color: {p.border}; max-height: 1px; min-height: 1px; border: none; }}
    #DialogButtons {{ background-color: {p.bg_secondary}; border-top: 1px solid {p.border}; }}
    #StepNumber {{ color: #ffffff; background-color: {p.accent};
                      border-radius: 11px; font-weight: bold; }}
    """)


def umschalten(app: QGuiApplication) -> Modus:
    """Wechselt zwischen hell und dunkel und wendet den Wechsel an.

    Fuer den Umschalter in der Werkzeugleiste. Die Anwendung muss danach nur
    noch zweierlei tun: den neuen Modus speichern und ihre selbstgezeichneten
    Flaechen neu einfaerben.

    Args:
        app:
            Die laufende Anwendung.

    Returns:
        Der neue Modus - zum Speichern.
    """
    setze_modus(umgeschaltet())
    anwenden(app)
    return _modus


def anwenden(app: QGuiApplication, dunkel: bool | None = None) -> Farben:
    """Setzt Stil, Palette und Stylesheet. Gibt die verwendeten Farben zurueck.

    Erneut aufrufen, wenn sich Erscheinungsbild, Akzentfarbe oder Zoom geaendert
    haben - Palette und Stylesheet haengen an der Anwendung, nicht am Fenster,
    und werden dabei vollstaendig neu gebaut:

        setze_modus(Modus.DUNKEL)
        anwenden(app)

    Was eine Anwendung selbst zeichnet (Kalender, Diagramme), erfaehrt davon
    nichts. Sie muss ihre Flaechen danach selbst neu einfaerben - die Farben
    dafuer liefert der Rueckgabewert.

    Args:
        app:
            Die laufende Anwendung.
        dunkel:
            Erzwingt hell oder dunkel, ohne das eingestellte Erscheinungsbild
            zu aendern. Ohne Angabe gilt die Einstellung.

    Returns:
        Die verwendeten Farben.
    """
    p = farben(dunkel)
    setze_stil = getattr(app, "setStyle", None)
    if callable(setze_stil):
        setze_stil("Fusion")
    app.setPalette(baue_palette(p))
    setze_qss = getattr(app, "setStyleSheet", None)
    if callable(setze_qss):
        setze_qss(baue_qss(p))
    return p
