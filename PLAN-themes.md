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

---

## Offen seit 11.09.2026: Auswahl zusammenlegen und kuratieren

Michael nach dem ersten Start von SiteHammer 0.3.0: die drei Felder kollidieren.
Erscheinungsbild, Akzentfarbe und Farbschema sind drei Achsen, von denen zwei
wirkungslos werden, sobald ein Schema gewählt ist. Der Hinweistext muss das
erklären - und ein Hinweis, der eine Bedienung erklären muss, ist meist die
falsche Bedienung.

**Sein Vorschlag:** alles in ein Feld. Der Hell/Dunkel-Toggle entfällt, die
Standardpalette erscheint als "Standard (Orange)", "Standard (Grün)" und so
weiter. Dazu die Themes kuratieren statt alle vierzig anzubieten.

### Die Kuratierung ist gemessen, nicht geraten

Kontrast haben alle 40 bestanden - das sagt aber nur, dass nichts unlesbar ist,
nicht ob man acht Stunden davor sitzen mag. Das bessere Maß ist die Sättigung
des Fenstergrunds: ein kräftig eingefärbter Grund ermüdet, ein entsättigter
nicht.

| Theme | Art | Sättigung | Textkontrast |
| --- | --- | ---: | ---: |
| classic-terminal | dunkel | 0 % | 14,6 |
| next | dunkel | 0 % | 10,9 |
| minty | dunkel | 0 % | 11,6 |
| gemstone | hell | 0 % | 15,4 |
| cupertino | hell | 1 % | 15,5 |
| clipper | hell | 6 % | 15,7 |
| plan9 | hell | 8 % | 18,7 |
| brick | hell | 11 % | 10,3 |
| hercules | dunkel | 18 % | 9,9 |
| corleone | dunkel | 21 % | 10,7 |
| bebox | dunkel | 22 % | 9,1 |

Danach kommt eine Lücke: der nächste ist beastie mit 30 %, und es geht bis
commandr mit 100 %. **Elf Themes unter 25 Prozent, dann ein Sprung** - die
Grenze liegt in den Daten, nicht im Geschmack.

Brotkasten steht bei 69 % und erklärt damit, warum Michael es als schwer
lesbar empfand. Nicht der Kontrast war zu niedrig (7,3 ist reichlich), sondern
die Fläche zu kräftig.

Das Messkript lag in `/tmp/saettigung.py` und rechnet mit `colorsys` über
`colors_from_palette()` - drei Zeilen, jederzeit wiederholbar.

### Der Haken am Zusammenlegen

Michael hat das Erscheinungsbild fest auf "Hell" stehen, nutzt die Modus-Wahl
also. Verschwindet der Toggle, muss sie in die Liste, sonst geht genau seine
Einstellung verloren. Also nicht `Standard (Orange)`, sondern zehn Einträge:
`Standard hell (Orange)` bis `Standard dunkel (Violett)`. Mit den elf Themes
ergibt das 21 Einträge - lang, aber vollständig und auf einen Blick.

### Die offene Entscheidung

Was wird aus "Wie das Betriebssystem"? Heute die Vorgabe. Mit fünf Akzenten
wären es 15 Standard-Einträge statt 10.

- **Streichen.** Wer ein Farbschema wählt, will ein bestimmtes Aussehen, und
  "richte dich nach Windows" ist das Gegenteil. Der Preis: ein Erstanwender
  bekommt bei hellem System eine helle Oberfläche nur, weil die Vorgabe
  zufällig passt, nicht weil die Anwendung sich anpasst.
- **Als einzelner erster Eintrag behalten**, ohne Akzentvariante, mit Orange.
  Dann 22 Einträge.

Michael denkt darüber nach (11.09.2026). Bis dahin bleibt die Oberfläche wie
sie ist - der Stand läuft.

### Was beim Umbau mitzumachen wäre

- Den Toggle aus dem Ansicht-Menü und aus `_erscheinungsbild_wechseln` nehmen.
- Die gespeicherten Einstellungen wandern lassen: aus `modus` plus `akzent`
  wird ein Schemaname, damit "Hell + Orange" nach dem Update genauso dasteht.
- Die Felder Erscheinungsbild und Akzentfarbe aus dem Dialog der Bibliothek
  entfernen - das betrifft auch jira-timesheet-qt.

### Warum das bei Qt anders liegt als im Terminal

Michael am 11.09.2026: "die meisten Themes sehen nicht gut aus bei Qt, das ist
mir bei Visual Studio Code schon aufgefallen." Das deckt sich mit der Messung
und liefert die Erklärung dazu:

- **Im Editor ist der Grund größtenteils von Text bedeckt.** Der Charakter
  eines Themes kommt aus der Syntaxfärbung, die Fläche selbst sieht man kaum.
  In einer Desktop-Anwendung ist der Grund der überwiegende Bildanteil.
- **Eine Oberfläche besteht aus vielen kleinen Flächen mit Rändern:** Knöpfe,
  Eingabefelder, Reiter, Menüs, Bildlaufleisten, Kopfzeilen. Jede braucht eine
  eigene Abstufung. Bei einem entsättigten Grund sind das Helligkeitsstufen -
  bei einem gesättigten werden daraus Farbabstufungen, und die wirken schnell
  schmutzig.
- Ein Terminal kennt diese Abstufungen gar nicht: dort gibt es sechzehn Farben
  und keine Ränder.

Das ist auch der Grund, warum die Ableitung nichts daran ändern kann. Sie sorgt
dafür, dass nichts unlesbar wird - dass eine Fläche ruhig genug für einen
Arbeitstag ist, kann sie nicht herstellen.

### Korrektur: nicht die Sättigung zählt, sondern S mal V (11.09.2026)

Michaels Auswahl nach dem Ansehen hat die Messung von oben widerlegt. Seine
zehn Guten: Motif, Gemstone, Clipper, Cupertino, Classic Navy, Bunty, BeBox,
Beastie, Corleone, Ascot. Fünf davon lagen über meiner 25-Prozent-Grenze,
Bunty sogar bei 100 Prozent Sättigung.

Der Grund: **die Farbmenge einer Fläche ist das Produkt aus Sättigung und
Helligkeit, nicht die Sättigung allein.**

| | Sättigung | Helligkeit | S mal V | Urteil |
| --- | ---: | ---: | ---: | --- |
| Bunty | 100 % | 17 % | 17,3 % | gut |
| Brotkasten | 69 % | 54 % | 37,3 % | schwer lesbar |

Ein fast schwarzes Aubergine darf hochgesättigt sein - bei 17 Prozent
Helligkeit sieht man die Farbigkeit kaum. Ein mittelhelles Blauviolett bei
54 Prozent dagegen schon.

**Die Grenze liegt zwischen 31,4 und 37,3 Prozent.** Michaels gesamte Auswahl
liegt darunter, Brotkasten darüber. Nur fünf Themes überschreiten sie: boing,
brotkasten, commandr, luna, metropolis. Das Messkript stand in `/tmp/chroma.py`
und rechnet über `colorsys` auf `colors_from_palette()`.

Das heißt auch: **die Kuratierung muss nicht auf elf schrumpfen.** 35 der 40
liegen unter der Grenze. Welche davon Michael tatsächlich mag, entscheidet
weiter der Augenschein - er sieht sich die übrigen noch an.

### Ein echter Fehler, gefunden an Classic Navy (11.09.2026)

Michael: "Classic Navy geht auch, aber aktivierte Toggles gehen unter."
Nachgemessen war es kein Problem dieses Schemas, sondern überall:

Ein eingerasteter Werkzeugknopf trug allein `accent_subtle`, eine
durchscheinende Fläche mit 20 Prozent Deckkraft. Gegen ihren Untergrund kam
die über alle 40 Schemata und beide Grundpaletten auf **1,16 bis 1,68** - der
schlechteste Fall ist ausgerechnet die Standardpalette hell mit 1,17. Weniger,
als eine Trennlinie erreichen muss, und die zeigt keinen Zustand an.

Behoben in `bfee1650`: `:checked` bekommt zusätzlich einen Rahmen in
Akzentfarbe, damit mindestens 3,17 statt 1,16. Der ruhende Knopf trägt
`1px solid transparent`, sonst springt die Leiste beim Einrasten.

**Die Lehre über den Fall hinaus:** eine durchscheinende Fläche ist kein
Zustandsmerkmal. Sie liegt per Bauart dicht an ihrem Untergrund - was sie
markiert, muss zusätzlich eine eigene Kante oder Farbe haben. Der Fehler fiel
nur deshalb an einem Retro-Schema auf, weil dort mehr Leute hinsehen als auf
eine Palette, die man seit einem Jahr kennt.
