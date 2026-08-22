"""Sinnbilder fuer die Werkzeugleiste.

Material Design Icons ueber QtAwesome. Die Glyphen sind Apache 2.0 lizenziert,
also deckungsgleich mit diesem Projekt, und lassen sich zur Laufzeit in jeder
Farbe zeichnen - das loest das fehlende currentColor in Qt-Stylesheets.

Die Anwendung spricht die Sinnbilder unter eigenen Namen an. Faellt QtAwesome
aus, kommt ein leeres QIcon zurueck statt einer Ausnahme: eine fehlende Grafik
darf die Werkzeugleiste nicht verhindern.
"""

from __future__ import annotations

import logging

from PySide6.QtGui import QIcon

logger = logging.getLogger(__name__)

# Sprechender Name -> Glyph. Anwendungen sprechen die Sinnbilder unter diesen
# Namen an, nicht ueber die mdi6-Kennung - so laesst sich ein Glyph an EINER
# Stelle austauschen. Namen aus jira-timesheet-qt uebernommen.
GLYPHEN: dict[str, str] = {
    "pruefen": "mdi6.play",
    "abbrechen": "mdi6.stop",
    "site_neu": "mdi6.plus",
    "site_bearbeiten": "mdi6.pencil-outline",
    "site_loeschen": "mdi6.trash-can-outline",
    "aktualisieren": "mdi6.refresh",
    "protokoll": "mdi6.text-box-outline",
    "einstellungen": "mdi6.tune-variant",
    "ueber": "mdi6.information-outline",
    "suchen": "mdi6.magnify",
    "bericht": "mdi6.file-document-outline",
}


def lade_icon(name: str, farbe: str) -> QIcon:
    """Liefert das Sinnbild in der gewuenschten Farbe."""
    glyph = GLYPHEN.get(name)
    if glyph is None:
        logger.warning("Unbekanntes Sinnbild: %s", name)
        return QIcon()
    try:
        import qtawesome as qta

        icon = qta.icon(glyph, color=farbe)
        return icon if isinstance(icon, QIcon) else QIcon()
    except Exception:
        logger.exception("Sinnbild '%s' konnte nicht geladen werden", name)
        return QIcon()
