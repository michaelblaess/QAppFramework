# QAppFramework

<p align="center">
  <img src="docs/flags/gb.svg" height="13" alt=""> <b>English</b> ·
  <img src="docs/flags/de.svg" height="13" alt=""> <a href="README.de.md">Deutsch</a>
</p>

---

[![License](https://img.shields.io/badge/license-BUSL--1.1-3b82f6)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776ab)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.8+-41cd52)](https://doc.qt.io/qtforpython/)

Shared building blocks for PySide6 desktop applications: a conservative theme,
runtime-colourable icons, and the dialogs that every application needs anyway.

## Why it exists

Because copying does not scale. While building the second Qt application, two
differences to the first crept in within an hour - both while copying values by
hand, both spotted afterwards in screenshots:

| | first application | second one (wrong) |
| --- | --- | --- |
| accent, light | `#e8590c` orange | `#2f6690` steel blue |
| icon size | 24 (Qt default) | 16 |

The accent colour paints the active tab. It **is** the recognition. So it lives
here once instead of being copied and quietly drifting apart.

The goal is plain: someone who moves from one of these applications to the next
should not have to relearn anything.

## Install

```toml
dependencies = [
    "QAppFramework @ git+https://github.com/michaelblaess/QAppFramework.git",
]
```

## Use

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
farben = anwenden(app)                       # Fusion + palette + stylesheet

icon = lade_icon("aktualisieren", farben.text_primary)

store = DisclaimerStore(Path.home() / ".my-tool" / "disclaimer.json")
if store.accepted_version != DISCLAIMER_VERSION:
    if DisclaimerDialog("my-tool 1.0").exec() != QDialog.DialogCode.Accepted:
        raise SystemExit(0)
    store.record()

window = MyWindow()
einhaengen(window, kopfzeile="my-tool 1.0")  # error dialog instead of a silent exit
abbruch_abfangen(app)                        # Ctrl+C shuts down in an orderly way
window.show()
app.exec()
```

## What is in here

| Module | Contents |
| --- | --- |
| `theme` | `Farben` palette (light and dark), `baue_palette`, `baue_qss`, `anwenden`, plus appearance, accent colour and zoom as module state |
| `icons` | `lade_icon(name, colour)` over QtAwesome, named glyphs in `GLYPHEN` |
| `about` | `AboutDialog` including the quote pool shipped as package data |
| `einstellungen` | `BasisEinstellungenDialog` with the Appearance and Storage pages |
| `absturz` | `FehlerDialog` and `einhaengen()` instead of a silent exit, `abbruch_abfangen()` for orderly Ctrl+C |
| `disclaimer` | `DisclaimerDialog`, `DisclaimerStore`, the shared liability wording |
| `zelle` | `ZellDelegate` - cell padding on the right and match highlighting |
| `farbe` | normalising colour input |
| `texte` | the handful of bilingual words the library itself needs |

### The settings dialog knows nothing about storage

One application has a typed class with `save()`, another an inheritance chain in
SQLite. A shared data model would only exist if both bent out of shape. The base
dialog therefore hands back only what it sets itself - appearance, accent, zoom -
and the application reads everything else from its own fields in `uebernehmen()`.

Four hooks carry it: `eigene_seiten()`, `uebernehmen()`, `speicherorte()` and
`darstellung_erweitern(form)`. The last one is the one people forget: your own
highlight colours belong **on** the Appearance page, not on a second page just
because the library owns the first.

### The disclaimer wording is fixed on purpose

Title, intro and the individual duties can be replaced per application. **The
liability paragraph cannot** - it should read the same everywhere. Change it and
`DISCLAIMER_VERSION` has to move too, otherwise nobody who already agreed will
ever see the new text.

## What is deliberately not in here

Anything only one application needs. A building block moves in here once the
**second** application uses it, not before.

## Development

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
uv run mypy src
```

`py.typed` ships with the package (PEP 561), so consuming applications get the
types without an override.

## License

**Business Source License 1.1** (see [LICENSE](LICENSE)). Reading, building and
using it yourself in your own projects is free as a private person, as long as
the result is not offered to third parties for a fee. Use by organizations or in
commercial products requires a commercial licence - just get in touch. Every
version turns into the **Mozilla Public License 2.0** four years after its
release.

The bundled Material Design Icons (via QtAwesome) remain Apache-2.0.
