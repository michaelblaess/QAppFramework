# Plan: die 40 Retro-Themes in den Qt-Anwendungen

Stand 10.09.2026. Michaels Entscheidung an diesem Tag: **alle 40 auswählbar**,
die Farbdaten kommen aus **einer** Quelle statt aus einer Kopie.

Vorarbeit ist der Wegwerf-Prototyp an SiteHammer vom selben Tag. Die Befunde
stehen im Skill `qt-specialist` unter "Terminal-Themes auf QSS abbilden".

**Randbedingung von Michael:** keine Abhängigkeit zu `retro-amp`. Das ist eine
Anwendung, keine Bibliothek - die Rechenfunktionen werden hier neu geschrieben,
nicht von dort importiert.

---

## Schritt 1 - textual-themes aufteilen

Heute sind die 40 Themes `textual.theme.Theme`-Objekte, und das Paket hängt an
`textual>=0.85`. Eine Qt-Anwendung würde damit Textual in die Nuitka-Binary
ziehen - die Abhängigkeitsfalle aus dem `qt-specialist`.

Die Themes sind aber reine Literale mit zwölf Feldern. Also:

    src/textual_themes/
      palettes.py    neu: Palette-Dataclass und 40 Instanzen, kein Import
      themes.py      baut daraus die Theme()-Objekte, braucht textual

`pyproject.toml`: `dependencies` wird leer, `textual` wird ein Extra. Die TUIs
haben Textual ohnehin selbst, für sie ändert sich nichts - das Extra ist die
Dokumentation der Grenze, nicht ihre Durchsetzung.

**Kritisch:** `__init__.py` importiert heute alles aus `themes.py`. Damit zöge
jeder Import Textual herein und die Aufteilung wäre wirkungslos. Die
Theme-Konstanten müssen also entweder lazy nachgeladen werden (`__getattr__` auf
Modulebene, PEP 562) oder der Datenteil bekommt einen eigenen Einstieg. Ein Test
hält fest, dass `import textual_themes.palettes` ohne Textual durchläuft.

**Gegen Abschreibfehler:** `palettes.py` wird aus dem Syntaxbaum von `themes.py`
erzeugt, nicht von Hand getippt - 40 mal 12 Werte. Ein Test vergleicht danach
jedes Feld jedes Themes zwischen alter und neuer Quelle.

## Schritt 2 - die Ableitung in QAppFramework

Elf Grundfarben auf sechzehn Felder von `Colors`. Fünf sind abgeleitet, die
Mischanteile sind aus der Bestandspalette zurückgerechnet (siehe Skill).

`color.py` bekommt `blend` und `ensure_contrast` dazu - `contrast_ratio` und
`relative_luminance` liegen seit `48006c62` schon dort.

**Die Lehre aus 48006c62 gilt hier genauso:** gegen alle vier Flächentöne heben,
nicht nur gegen `bg_primary`. Der Prototyp hat das falsch gemacht, und man sieht
es an Brotkasten - der Fließtext trug, die inaktiven Reiter auf `bg_secondary`
blieben blass. Michael hat es sofort bemerkt.

Der bestehende `TestKontrast` wird auf die abgeleiteten Paletten ausgeweitet:
dieselben sieben Paare, alle 40 Themes, beide Erscheinungsbilder.

## Schritt 3 - Auswahl und Umschalten

- **Dropdown** im `BasisEinstellungenDialog` unter Darstellung, neben
  Erscheinungsbild, Akzent und Zoom. Alphabetisch, alle 40. Damit haben beide
  Anwendungen es, ohne etwas zu tun.
- **Durchschalten per Taste** statt per Knopf in der Werkzeugleiste: die ist bei
  SiteHammer voll, und ein Knopf, der bei jedem Druck etwas anderes tut, lässt
  sich nicht beschriften. Der Themename kurz in die Statuszeile.
- Die Wahl wird gespeichert wie Modus, Akzent und Zoom - also als weiteres Feld
  in `Appearance`.

**Offen:** ob das Theme den Akzent mitbringt oder ob Michaels fünf Akzentfarben
darüber liegen. Ein Theme hat einen eigenen Akzent, und ihn zu überschreiben
nimmt ihm den Charakter. Am Prototyp trug der Theme-Akzent. Vorschlag: das Theme
setzt ihn, die Akzentauswahl bleibt für die Standardpalette.

## Schritt 4 - was selbst gezeichnet wird

`apply_theme()` sagt es im eigenen Docstring: was eine Anwendung selbst zeichnet,
erfährt vom Wechsel nichts. In SiteHammer sind das die Tabellenmodelle
(`herkunft_modell`, `konsolen_modell`), in jira-timesheet-qt der Kalender. Beide
holen ihre Farben über `colors()` und müssen nach einem Wechsel neu einfärben -
`MainWindow._erscheinungsbild_anwenden()` ist der Ort, der das heute schon für
Modus und Akzent tut.

**Ungeprüft und deshalb der erste Punkt beim Bauen:** ob das dort wirklich
vollständig passiert. Der Prototyp hat immer neu gestartet und konnte es nicht
zeigen.

---

## Stand: alle vier Schritte erledigt (10.09.2026)

| Schritt | Commit | Ergebnis |
| --- | --- | --- |
| 1 textual-themes aufteilen | `a86ff9cb` | 520 Feldwerte verglichen, 0 Abweichungen |
| 2 Ableitung | `88b682ea` | 40 von 40 Themes erreichen alle sechs Ziele |
| 3 Auswahl und Umschalten | `9d12ee51`, `41cbb460` | Feld in beiden Anwendungen, Strg+T in SiteHammer |
| 4 Selbstgezeichnetes | - | war bereits gelöst |

**Schritt 4 war keiner.** `_erscheinungsbild_anwenden()` in SiteHammer färbt
die selbstgezeichneten Reiter und die Sinnbilder ohnehin schon neu - am
laufenden Fenster nachgesehen, sechs Wechsel hintereinander, alles zieht mit.
Der Plan hatte das als offenen Punkt geführt, weil der Prototyp für jedes
Theme neu gestartet war und es nicht zeigen konnte.

**Was beim Bauen dazukam und im Plan fehlte:**

- Ein Repo, das `textual-themes` **selbst** pinnt, muss beide Pins ziehen -
  sonst gewinnt der ältere gegen den der Bibliothek, und der Start scheitert an
  `textual_themes.palettes`. Betrifft SiteHammer, weil es eine TUI hat.
- Die Abfrage hieß zuerst `theme()` und verdeckte das gleichnamige Modul.
  Sie heißt `current_theme()`.
- In jira-timesheet-qt ist `theme` seit jeher das Erscheinungsbild. Das
  Farbschema steht dort unter `color_scheme`.
- Zwei neue Glyphen brauchten einen Test: `load_icon` gibt bei einem
  unbekannten Namen absichtlich ein leeres QIcon zurück, ein Tippfehler fällt
  also nur als Lücke in der Werkzeugleiste auf.

**Der offene Punkt aus Schritt 3 ist entschieden:** das Theme bringt seinen
Akzent mit. Michaels fünf Akzentfarben gelten weiter für die Standardpalette.

## Was bewusst offen bleibt

- **Durchschalten in jira-timesheet-qt.** Dort gibt es nur das Auswahlfeld.
  Die Werkzeugleiste ist voller als in SiteHammer, und ob Strg+T dort frei
  ist, wurde nicht geprüft.
- **Tabellen mit echten Daten.** Geprüft wurde am Leerzustand und am
  Einstellungsdialog. Zeilenwechselfarben und Markierungen in gefüllten
  Tabellen hat noch niemand gegen ein Retro-Schema gesehen.
- **Der Kalender in jira-timesheet-qt** zeichnet selbst und hat ein eigenes
  `apply_mode(mode)` - er kennt hell und dunkel, nicht das Farbschema.
