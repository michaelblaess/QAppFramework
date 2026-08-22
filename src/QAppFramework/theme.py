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

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette


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

# Qt liefert fuer Werkzeugleisten von sich aus 24 Pixel. jira-timesheet-qt setzt
# nichts anderes, also wird hier ebenfalls nichts gesetzt. Der Wert steht nur
# als Erwartung fuer den Test, nicht als Vorgabe an die Leiste.
TOOLBAR_ICON_SIZE = 24


def ist_dunkel() -> bool:
    """Fragt das Farbschema des Systems ab (Qt 6.5 und neuer)."""
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return True


def farben(dunkel: bool | None = None) -> Farben:
    return DUNKEL if (ist_dunkel() if dunkel is None else dunkel) else HELL


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


def baue_qss(p: Farben) -> str:
    """Struktur und Schrift.

    Die Bloecke fuer Werkzeugleiste und Reiter sind woertlich aus
    jira-timesheet-qt uebernommen - Abstaende, Schriftstaerken und Farben
    inbegriffen. Wer hier etwas aendert, bricht die Wiedererkennung.
    """
    return f"""
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

    QDockWidget::title {{ background-color: {p.bg_secondary}; padding: 5px 8px;
                          border-top: 1px solid {p.border}; }}

    #Stat {{ border: 1px solid {p.border}; border-radius: {RADIUS_SM}px; padding: 2px 8px; }}
    #EmptyTitle {{ font-size: 19px; font-weight: bold; }}
    #EmptyText {{ color: {p.text_secondary}; }}
    #Hint {{ color: {p.text_secondary}; }}
    #StepNumber {{ color: #ffffff; background-color: {p.accent};
                      border-radius: 11px; font-weight: bold; }}
    """


def anwenden(app: QGuiApplication, dunkel: bool | None = None) -> Farben:
    """Setzt Stil, Palette und Stylesheet. Gibt die verwendeten Farben zurueck."""
    p = farben(dunkel)
    setze_stil = getattr(app, "setStyle", None)
    if callable(setze_stil):
        setze_stil("Fusion")
    app.setPalette(baue_palette(p))
    setze_qss = getattr(app, "setStyleSheet", None)
    if callable(setze_qss):
        setze_qss(baue_qss(p))
    return p
