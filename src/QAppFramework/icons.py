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
import tempfile
from pathlib import Path

from PySide6.QtGui import QIcon

from .color import normalize

logger = logging.getLogger(__name__)

# Sprechender Name -> Glyph. Anwendungen sprechen die Sinnbilder unter diesen
# Namen an, nicht ueber die mdi6-Kennung - so laesst sich ein Glyph an EINER
# Stelle austauschen. Namen aus jira-timesheet-qt uebernommen.
GLYPHS: dict[str, str] = {
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
    "erscheinungsbild": "mdi6.theme-light-dark",
    # Beim Durchschalten der Farbschemata. Zwei verschiedene Glyphen, weil
    # dieselbe Palette fuer beide Richtungen nichts unterscheidet.
    "farbschema_weiter": "mdi6.palette-advanced",
    "farbschema_zurueck": "mdi6.palette-outline",
}


# Wohin die Zeichen fuer Kontrollkaestchen geschrieben werden. Ein
# Stylesheet kann Bilder nur ueber einen Dateipfad einbinden - eine
# data:-URL nimmt Qt nicht an, am 11.09.2026 gemessen. Die Dateien sind
# jederzeit neu erzeugbar, deshalb das Temp-Verzeichnis.
_ZEICHENORDNER = Path(tempfile.gettempdir()) / "QAppFramework-indicators"


def indicator_image(glyph: str, farbe: str, groesse: int = 13) -> str:
    """Schreibt ein Sinnbild als PNG und gibt den Pfad fuer ein Stylesheet.

    Fuer Kontrollkaestchen und Optionsfelder. Sobald ein Stylesheet
    `::indicator` anfasst, zeichnet Qt den Indikator nicht mehr selbst -
    auch das Haekchen nicht. Es muss also als Bild kommen, und Bilder kennt
    ein Stylesheet nur als Datei.

    Der Dateiname enthaelt Glyph, Farbe und Groesse: ein Themewechsel
    ueberschreibt damit nichts, und ein zweiter Aufruf kostet nichts.

    Args:
        glyph:
            Die mdi6-Kennung, etwa "mdi6.check-bold".
        farbe:
            In welcher Farbe gezeichnet wird.
        groesse:
            Kantenlaenge in Bildpunkten.

    Returns:
        Der Pfad mit Schraegstrichen, wie ihn `url()` erwartet. Leer, wenn
        das Zeichen nicht erzeugt werden konnte - der Aufrufer laesst die
        Bildregel dann weg, statt auf ein fehlendes Bild zu verweisen.
    """
    sicher = f"{glyph}-{normalize(farbe)}-{groesse}".replace(".", "_")
    ziel = _ZEICHENORDNER / f"{sicher}.png"
    if ziel.is_file():
        return ziel.as_posix()

    try:
        import qtawesome as qta

        _ZEICHENORDNER.mkdir(parents=True, exist_ok=True)
        pixmap = qta.icon(glyph, color=farbe).pixmap(groesse, groesse)
        if pixmap.isNull() or not pixmap.save(str(ziel), "PNG"):
            return ""
    except Exception:  # pragma: no cover - haengt an der Umgebung
        # Ohne laufende QApplication gibt es keine QPixmap. Das ist in
        # Tests der Normalfall und kein Grund, das Stylesheet zu verlieren.
        logger.debug("Zeichen '%s' konnte nicht erzeugt werden", glyph, exc_info=True)
        return ""
    return ziel.as_posix()


def load_icon(name: str, farbe: str) -> QIcon:
    """Liefert das Sinnbild in der gewuenschten Farbe."""
    glyph = GLYPHS.get(name)
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
