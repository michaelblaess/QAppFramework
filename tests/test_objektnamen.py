"""Die Objektnamen der Bibliothek sind ihr Vertrag mit den Anwendungen.

Setzt eine Anwendung `EmptyTitle`, muss die zugehoerige Regel greifen. Ein
Tippfehler oder eine Umbenennung faellt sonst erst auf, wenn jemand das Fenster
oeffnet - die Beschriftung sieht dann einfach aus wie jede andere.

Geprueft wird deshalb die WIRKUNG, nicht der Name: ein Widget mit dem Namen
wird gezeichnet und mit einem namenlosen verglichen. Ein Namensvergleich gegen
dieselbe Datei, aus der die Namen stammen, koennte nichts finden.
"""

from __future__ import annotations

import os
import re

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6", reason="Erscheinungsbild gehoert zur Desktop-Oberflaeche")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402

from QAppFramework.theme import HELL, baue_qss  # noqa: E402


def _namen() -> list[str]:
    """Alle Objektnamen aus dem Stylesheet - ohne Unterelemente wie ::tab.

    Aus dem Stylesheet gelesen statt von Hand gepflegt: so wird jeder neu
    hinzugefuegte Name automatisch mitgeprueft.
    """
    treffer = re.findall(r"#([A-Za-z][A-Za-z0-9_]*)\s*(?:\{|::|\[)", baue_qss(HELL))
    return sorted(set(treffer))


@pytest.fixture(scope="module")
def app() -> QApplication:
    vorhanden = QApplication.instance()
    return vorhanden if isinstance(vorhanden, QApplication) else QApplication([])


def _gezeichnet(app: QApplication, name: str) -> bytes:
    """Zeichnet eine Beschriftung mit diesem Objektnamen und gibt die Bildpunkte.

    Zwei Dinge sind noetig, damit der Vergleich etwas taugt:

    Das Widget wird gezeigt (aber nicht auf den Schirm gelassen), sonst ist das
    Layout noch nicht durch und das Bild faellt mal mit, mal ohne fertige
    Auszeichnung aus - der Test schlug daraufhin gelegentlich fehl, ohne dass
    sich etwas geaendert hatte.

    Und gezeichnet wird in ein vorgefuelltes Bild statt ueber grab(): dessen
    Pixmap ist dort, wo das Widget nichts malt, uninitialisiert. Zwei Aufnahmen
    desselben Widgets unterschieden sich damit zuverlaessig - gemessen.

    Das QImage braucht eine eigene Variable. Bei toImage().constBits() gibt
    Python das Bild frei, bevor die Bildpunkte gelesen sind - der Zeiger
    zeigt dann auf fremden Speicher, und die ersten Bytes wechselten von
    Aufruf zu Aufruf (01000000 / 500143f6, gemessen). Der Test fiel dadurch
    in zwei von zehn Laeufen, ohne dass sich etwas geaendert hatte.
    """
    app.setStyleSheet(baue_qss(HELL))
    label = QLabel("Beispiel")
    label.setObjectName(name)
    label.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
    label.resize(220, 44)
    label.show()
    app.processEvents()
    bild = QPixmap(220, 44)
    bild.fill(Qt.GlobalColor.magenta)
    label.render(bild)
    aufnahme = bild.toImage()
    punkte = aufnahme.constBits().tobytes()
    label.close()
    return punkte


class TestObjektnamen:
    @pytest.mark.parametrize("name", _namen())
    def test_der_name_veraendert_die_darstellung(self, app: QApplication, name: str) -> None:
        """Jeder Name im Stylesheet muss sichtbar etwas bewirken."""
        assert _gezeichnet(app, name) != _gezeichnet(app, ""), (
            f"#{name} steht im Stylesheet, aendert aber nichts an der Darstellung"
        )

    def test_die_pruefung_kann_scheitern(self, app: QApplication) -> None:
        """Gegenprobe: ein Name ohne Regel darf sich NICHT vom namenlosen unterscheiden.

        Ohne diese Zusicherung waere der Test oben auch dann gruen, wenn das
        Zeichnen gar nichts misst.
        """
        assert _gezeichnet(app, "GibtEsNicht") == _gezeichnet(app, "")

    def test_die_alten_deutschen_namen_wirken_nicht_mehr(self, app: QApplication) -> None:
        """Sie hiessen bis zum 23.08.2026 so. Wer sie noch setzt, bekommt nichts."""
        for veraltet in ("LeerTitel", "LeerText", "LeerKarte", "Hinweis", "Kennzahl", "SchrittNummer"):
            assert _gezeichnet(app, veraltet) == _gezeichnet(app, ""), (
                f"#{veraltet} wirkt noch - die Umbenennung ist unvollstaendig"
            )
