"""Die Fenstertitelleiste mitfaerben - unter Windows.

Die Titelleiste zeichnet das Betriebssystem, nicht Qt. Bei einem dunklen
Theme stand deshalb ein helles Windows-Band ueber einer dunklen
Oberflaeche - Michael hat das am 11.09.2026 an einem Dialog gezeigt.

Seit Windows 11 (Build 22000) nimmt `DwmSetWindowAttribute` Farben fuer
Titelleiste, Titeltext und Fensterrahmen entgegen. Geprueft an Build
26200: alle vier Aufrufe liefern S_OK.

Auf macOS und Linux tut dieses Modul nichts. Dort folgt die Dekoration
ohnehin dem Fenstermanager, und ein Eingriff waere jedes Mal ein anderer.

Public API:
    - `style_window()` - ein einzelnes Fenster einfaerben.
    - `style_all_windows()` - alle offenen Fenster der Anwendung.
    - `watch_new_windows()` - kuenftige Fenster gleich mit erfassen.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QWidget

from .color import is_light, normalize
from .theme import Colors, colors

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

# Aus dwmapi.h. Die drei Farbattribute gibt es erst ab Windows 11 - auf
# aelteren Fassungen liefert der Aufruf einen Fehlercode, den wir schlucken.
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36

_LAEUFT_AUF_WINDOWS = sys.platform == "win32"


def _colorref(hexwert: str) -> int:
    """Rechnet '#RRGGBB' in Windows' COLORREF um.

    COLORREF ist 0x00BBGGRR - die Kanaele stehen umgekehrt zu HTML. Wer
    das uebersieht, bekommt eine Titelleiste in der Komplementaerfarbe und
    sucht den Fehler lange im Theme.
    """
    roh = normalize(hexwert)
    rot, gruen, blau = (int(roh[i : i + 2], 16) for i in (0, 2, 4))
    return (blau << 16) | (gruen << 8) | rot


def style_window(widget: QWidget, farben: Colors | None = None) -> bool:
    """Faerbt die Titelleiste eines Fensters passend zum Theme.

    Args:
        widget:
            Das Fenster. Ein Widget mit Elternteil hat keine eigene
            Titelleiste und wird uebergangen.
        farben:
            Die Palette. Ohne Angabe die gerade geltende.

    Returns:
        True, wenn die Farben gesetzt wurden. False auf anderen
        Betriebssystemen, bei aelteren Windows-Fassungen und immer dann,
        wenn das Fenster noch kein Fensterhandle hat.
    """
    if not _LAEUFT_AUF_WINDOWS or not widget.isWindow():
        return False

    p = farben if farben is not None else colors()
    try:
        import ctypes
        from ctypes import wintypes

        kennung = int(widget.winId())
        if not kennung:
            return False

        dwm = ctypes.WinDLL("dwmapi")

        def setze(attribut: int, wert: int) -> int:
            roh = ctypes.c_int(wert)
            return int(
                dwm.DwmSetWindowAttribute(
                    wintypes.HWND(kennung),
                    ctypes.c_uint(attribut),
                    ctypes.byref(roh),
                    ctypes.sizeof(roh),
                )
            )

        # Zuerst das Erscheinungsbild: davon haengen die Systemknoepfe ab
        # (Minimieren, Maximieren, Schliessen). Sie folgen dem Flag, nicht
        # der Farbe - ohne das waeren sie weiss auf einem hellen Theme.
        setze(DWMWA_USE_IMMERSIVE_DARK_MODE, 0 if is_light(p.bg_secondary) else 1)

        # Die Titelleiste nimmt den Ton der Werkzeugleiste darunter, nicht
        # den Fenstergrund - so geht das Band optisch in die Leiste ueber.
        setze(DWMWA_CAPTION_COLOR, _colorref(p.bg_secondary))
        setze(DWMWA_TEXT_COLOR, _colorref(p.text_primary))
        setze(DWMWA_BORDER_COLOR, _colorref(p.accent if p.expressive else p.border))
    except Exception:  # pragma: no cover - haengt an der Windows-Fassung
        logger.debug("Titelleiste konnte nicht eingefaerbt werden", exc_info=True)
        return False
    return True


def style_all_windows(farben: Colors | None = None) -> int:
    """Faerbt alle offenen Fenster der Anwendung.

    Args:
        farben:
            Die Palette. Ohne Angabe die gerade geltende.

    Returns:
        Wie viele Fenster eingefaerbt wurden.
    """
    anwendung = QApplication.instance()
    if anwendung is None:
        return 0
    p = farben if farben is not None else colors()
    fenster: Sequence[QWidget] = [
        w for w in QApplication.topLevelWidgets() if isinstance(w, QWidget)
    ]
    return sum(1 for w in fenster if style_window(w, p))


class _Fensterwache(QObject):
    """Faerbt jedes Fenster, sobald es zum ersten Mal gezeigt wird.

    Ohne sie muesste jeder Dialog daran denken - und einer vergisst es
    immer. Der Filter haengt an der Anwendung und sieht jedes Show-Ereignis.
    """

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt gibt den Namen vor
        if event.type() == QEvent.Type.Show and isinstance(watched, QWidget) and watched.isWindow():
            style_window(watched)
        return False


_wache: _Fensterwache | None = None


def watch_new_windows() -> bool:
    """Sorgt dafuer, dass auch kuenftige Fenster eingefaerbt werden.

    Mehrfach aufrufbar - der Filter wird nur einmal eingehaengt.

    Returns:
        True, wenn die Wache steht.
    """
    global _wache
    if not _LAEUFT_AUF_WINDOWS:
        return False
    anwendung = QApplication.instance()
    if anwendung is None:
        return False
    if _wache is None:
        _wache = _Fensterwache()
        anwendung.installEventFilter(_wache)
    return True
