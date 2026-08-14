# handmade-qt

Shared building blocks for PySide6 desktop applications: a conservative theme,
runtime-colourable icons and the dialogs that every application needs anyway.

The point is consistency. Someone who moves from one of these applications to
the next should not have to relearn anything - so the theme lives here once
instead of being copied and quietly drifting apart.

Part of [handmade-software.de](https://handmade-software.de).

## Install

```toml
dependencies = [
    "handmade-qt @ git+https://github.com/michaelblaess/handmade-qt.git",
]
```

## Use

```python
from PySide6.QtWidgets import QApplication
from handmade_qt import anwenden, lade_icon, DisclaimerDialog, DisclaimerStore

app = QApplication([])
farben = anwenden(app)                      # Fusion + palette + stylesheet

icon = lade_icon("site_neu", farben.text_primary)

store = DisclaimerStore(Path.home() / ".my-tool" / "disclaimer.json")
if store.accepted_version != DISCLAIMER_VERSION:
    if DisclaimerDialog("my-tool 1.0").exec() != QDialog.DialogCode.Accepted:
        raise SystemExit(0)
    store.record()
```

## What is in here

| Module | Contents |
| --- | --- |
| `theme` | `Farben` palette (light and dark), `baue_palette`, `baue_qss`, `anwenden` |
| `icons` | `lade_icon(name, colour)` over QtAwesome, named glyphs in `GLYPHEN` |
| `disclaimer` | `DisclaimerDialog`, `DisclaimerStore`, the shared liability wording |

The disclaimer ships wording for tools that fetch remote systems and put load on
them. Title, intro and the individual duties can be replaced per application -
**the liability paragraph cannot**, on purpose: it should read the same
everywhere.

## What is deliberately not in here

Anything only one application needs. A building block moves in here once the
**second** application uses it, not before.

## License

Apache-2.0. The bundled Material Design Icons (via QtAwesome) are Apache-2.0 as
well.
