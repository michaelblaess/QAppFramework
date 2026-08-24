# QAppFramework

<p align="center">
  <img src="docs/flags/gb.svg" height="13" alt=""> <a href="README.md">English</a> ·
  <img src="docs/flags/de.svg" height="13" alt=""> <b>Deutsch</b>
</p>

---

[![License](https://img.shields.io/badge/license-BUSL--1.1-3b82f6)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776ab)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.8+-41cd52)](https://doc.qt.io/qtforpython/)

Gemeinsame Bausteine für PySide6-Desktop-Anwendungen: ein zurückhaltendes
Erscheinungsbild, zur Laufzeit einfärbbare Sinnbilder und die Dialoge, die jede
Anwendung ohnehin braucht.

## Warum es sie gibt

Weil Abschreiben nicht skaliert. Beim Bau der zweiten Qt-Anwendung sind mir
binnen einer Stunde zwei Abweichungen zur ersten unterlaufen - beide beim
Abschreiben von Werten, beide erst hinterher an Bildschirmfotos aufgefallen:

| | erste Anwendung | zweite (falsch) |
| --- | --- | --- |
| Akzent hell | `#e8590c` Orange | `#2f6690` Stahlblau |
| Symbolgröße | 24 (Qt-Vorgabe) | 16 |

Die Akzentfarbe färbt den aktiven Reiter. Sie **ist** die Wiedererkennung.
Deshalb liegt sie hier an einer Stelle, statt kopiert zu werden und still
auseinanderzulaufen.

Das Ziel ist schlicht: wer von einer dieser Anwendungen zur nächsten wechselt,
soll sich nicht umgewöhnen müssen.

## Einbinden

```toml
dependencies = [
    "QAppFramework @ git+https://github.com/michaelblaess/QAppFramework.git",
]
```

## Verwenden

```python
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog
from QAppFramework import (
    DISCLAIMER_VERSION,
    DisclaimerDialog,
    DisclaimerStore,
    abbruch_abfangen,
    anwenden,
    einhaengen,
    lade_icon,
)

app = QApplication([])
farben = anwenden(app)                       # Fusion + Palette + Stylesheet

icon = lade_icon("aktualisieren", farben.text_primary)

store = DisclaimerStore(Path.home() / ".mein-werkzeug" / "disclaimer.json")
if store.accepted_version != DISCLAIMER_VERSION:
    if DisclaimerDialog("mein-werkzeug 1.0").exec() != QDialog.DialogCode.Accepted:
        raise SystemExit(0)
    store.record()

fenster = MeinFenster()
einhaengen(fenster, kopfzeile="mein-werkzeug 1.0")  # Fehlerdialog statt wortlosem Abbruch
abbruch_abfangen(app)                              # Strg+C beendet geordnet
fenster.show()
app.exec()
```

## Was drin ist

| Modul | Inhalt |
| --- | --- |
| `theme` | `Farben` für hell und dunkel, `baue_palette`, `baue_qss`, `anwenden`, dazu Erscheinungsbild, Akzentfarbe und Zoom als Modulzustand |
| `icons` | `lade_icon(name, farbe)` über QtAwesome, sprechende Namen in `GLYPHEN` |
| `about` | `AboutDialog` samt Zitatpool in den Paketdaten |
| `einstellungen` | `BasisEinstellungenDialog` mit den Seiten Darstellung und Speicherort |
| `absturz` | `FehlerDialog` und `einhaengen()` statt wortlosem Abbruch, `abbruch_abfangen()` für geordnetes Strg+C |
| `disclaimer` | `DisclaimerDialog`, `DisclaimerStore`, der gemeinsame Haftungsabsatz |
| `zelle` | `ZellDelegate` - Innenabstand rechts und Trefferhervorhebung |
| `farbe` | Farbeingaben normalisieren |
| `texte` | die wenigen zweisprachigen Wörter, die die Bibliothek selbst braucht |

### Der Einstellungsdialog kennt die Ablage nicht

Eine Anwendung hat eine getypte Klasse mit `save()`, eine andere eine Vererbung
über mehrere Ebenen in SQLite. Ein gemeinsames Datenmodell gäbe es nur, wenn
sich beide verbiegen. Der Basisdialog reicht deshalb nur zurück, was er selbst
einstellt - Erscheinungsbild, Akzent, Zoom -, alles andere liest die Anwendung
in `uebernehmen()` aus ihren eigenen Feldern.

Vier Haken tragen das: `eigene_seiten()`, `uebernehmen()`, `speicherorte()` und
`darstellung_erweitern(formular)`. Der letzte ist der, den man vergisst:
app-eigene Markierungsfarben gehören **auf** die Darstellungs-Seite, nicht auf
eine zweite, nur weil die Bibliothek die erste hält.

### Der Haftungsabsatz ist mit Absicht fest

Titel, Einleitung und die einzelnen Pflichten lassen sich je Anwendung
ersetzen. **Der Haftungsabsatz nicht** - er soll überall gleich lauten. Wer ihn
ändert, muss `DISCLAIMER_VERSION` mitziehen, sonst bekommt niemand, der schon
zugestimmt hat, den neuen Text je zu sehen.

## Was bewusst nicht drin ist

Alles, was nur eine Anwendung braucht. Ein Baustein wandert erst hierher, wenn
ihn die **zweite** Anwendung ebenfalls verwendet.

## Entwicklung

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
uv run mypy src
```

`py.typed` liegt bei (PEP 561) - die einbindenden Anwendungen bekommen die
Typen also ohne eigenen Override.

## Lizenz

**Business Source License 1.1** (siehe [LICENSE](LICENSE)). Lesen, selbst bauen
und in eigenen Projekten verwenden ist als Privatperson kostenlos, solange das
Ergebnis nicht entgeltlich angeboten wird. Nutzung durch Organisationen oder in
kommerziellen Produkten braucht eine kommerzielle Lizenz - sprich mich einfach
an. Jede Version wird vier Jahre nach ihrer Veröffentlichung automatisch zur
**Mozilla Public License 2.0**.

Die mitgelieferten Material Design Icons (über QtAwesome) bleiben Apache-2.0.
