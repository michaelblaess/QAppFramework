# QAppFramework - Ausbau zur gemeinsamen Grundlage

**Erledigt am 23.08.2026** (0.9.0). Was hier als Plan stand, ist gebaut -
die Abschnitte bleiben als Begruendung stehen, warum es so aussieht.

Stand vorher: Ausgangslage: die Bibliothek trägt Farben, Sinnbilder und den
Haftungshinweis. Alles andere steht doppelt in jira-timesheet-qt und SiteHammer
oder fehlt in SiteHammer ganz.

## Entschieden

- **Reihenfolge:** jira-timesheet-qt zuerst umstellen. Dort kommt alles her,
  dort zeigt sich, ob der Schnitt trägt. SiteHammer erbt danach eine erprobte
  Basis.
- **ObjectNames englisch.** `#EmptyTitle`, `#Hint`, `#Stat` - QAppFramework und
  SiteHammer benennen um, jira-timesheet-qt führt die Konvention bereits.
- **Zweisprachig über einen `lang`-Parameter**, wie in textual-widgets. Jeder
  Dialog der Bibliothek trägt beide Textsätze, Vorgabe ist Deutsch.

## Warum das nicht mit dem About-Dialog anfangen kann

`theme.anwenden(app, dunkel=None)` liest einmal das Farbschema des Systems.
Es gibt keinen Modus-Zustand, keine Akzentfarbe und keinen Zoom. Weder der
Umschalter noch die Darstellungs-Seite der Einstellungen lassen sich darauf
bauen. jira-timesheet-qt hat das alles in seinem eigenen `ui/theme.py`
(774 Zeilen gegen 203 hier).

Dazu kommt: ein Baustein wandert nie allein, sein Stylesheet muss mit. Gemessen
am 22.08.2026 - 82 Selektoren dort, 27 hier. Von den 61 fehlenden sind rund 30
allgemein (`#About*`, `#Settings*`, `#Disclaimer*`, `#Toast*`, `QToolTip`,
`QSplitter::handle`, `QMainWindow::separator`, `QTableView`, `QMenu::icon`).

Der Beleg liegt schon vor: die Bibliothek liefert `DisclaimerDialog`, aber kein
`#Disclaimer*`-Stylesheet. Der Dialog behilft sich mit `#LeerTitel` und
`#Hinweis` und sieht in SiteHammer deshalb anders aus als in jira-timesheet-qt.

## Phasen

### 0 - ObjectNames auf Englisch

`LeerTitel` -> `EmptyTitle`, `LeerText` -> `EmptyText`, `LeerKarte` ->
`EmptyCard`, `Hinweis` -> `Hint`, `Kennzahl` -> `Stat`, `SchrittNummer` ->
`StepNumber`. Betrifft die Bibliothek und SiteHammer. Klein, aber zuerst -
danach folgt alles Neue derselben Konvention.

### 1 - Erscheinungsbild laufzeitfähig

- `Modus` (system/dunkel/hell), Akzentfarben je Modus, Zoomstufen
- `setze_akzent` / `setze_zoom` als Modul-Zustand, den `farben()` einrechnet
- `anwenden()` ohne Argumente wendet den aktuellen Zustand neu an
- fehlende Grundlagen im Stylesheet: `QToolTip`, `QSplitter::handle`,
  `QMainWindow::separator`, `QTableView`, `QMenu::icon`
- `texte.py` mit dem `lang`-Muster für alle Dialoge der Bibliothek

### 2 - Info-Dialog

Aus jira-timesheet-qt übernehmen, samt `#About*`-Stylesheet. Der Zitatpool
wandert mit: `sync_zitate.py` bekommt QAppFramework als Ziel, jira-timesheet-qt
fällt dort weg.

### 3 - Einstellungen als Basisdialog

Die Bibliothek trägt Gerüst und Bausteine, **nicht** die Persistenz -
jira-timesheet-qt hat eine Einstellungs-Dataclass, SiteHammer bekommt Vererbung
über Unternehmen, Site und Umgebung in SQLite. Ein gemeinsames Datenmodell gibt
es nicht und soll es nicht geben.

Eingebaut:
- Gerüst: Navigationsliste, Seitenstapel, Bildlaufbereich je Seite,
  Abbrechen/Speichern, Größengriff, Mindestbreiten-Rechnung
- Bausteine für die App-Seiten: `seite()`, `beschriftung()`, `hinweis()`,
  `auswahl()` (mit dem QListView-Popup), `farbknopf()`, `pfadzeile()`
- Seite **Darstellung** vollständig: Erscheinungsbild, Akzentfarbe, Zoom.
  Gibt ein Ergebnisobjekt zurück, die Anwendung speichert es wie sie will
- Seite **Speicherort** über den Haken `speicherorte() -> [(Text, Pfad)]`

Haken für die Anwendung: `eigene_seiten()` und `uebernehmen()`. Beide
eingebauten Seiten hängen hinten an - genau dort stehen sie heute schon.

### 4 - Umschalter Hell/Dunkel

Drei Teile: Umschaltlogik und Neuaufbau in die Bibliothek, das Speichern des
Modus bleibt bei der Anwendung, der Werkzeugleisten-Befehl ebenso. Was
`_reapply_theme` zusätzlich tut (Kalender, Summenleiste neu einfärben), bleibt
app-spezifisch - die Bibliothek gibt dafür nur ein Signal.

### 5 - jira-timesheet-qt umstellen

Eigenes `ui/theme.py`, `about_dialog.py`, `disclaimer_dialog.py` und das Gerüst
von `settings_dialog.py` fallen weg. Die app-spezifischen Stylesheet-Regeln
(`#Detail*`, `#MonthNav*`, `#Summary*`, `#AnonBadge`, Board-Teiler) bleiben dort
und werden an das Stylesheet der Bibliothek angehängt.

### 6 - SiteHammer nachziehen

Info-Dialog, Einstellungen mit Darstellung und Speicherort, Umschalter.

## Danach - belegte Lücken in SiteHammer

Keine Kür, sondern Mängel:

- **Absturzschutz.** jira-timesheet-qt hat einen (160 Zeilen), SiteHammer
  keinen. Ein unbehandelter Fehler beendet dort die Anwendung mitten im Lauf.
- **Zellen-Innenabstand.** jira-timesheet-qt zeichnet ihn über einen Delegate
  (152 Zeilen), SiteHammer hat fünf Tabellen ohne. Qt gibt dem Zelltext vier
  Pixel bis zur Kante.

## Wenn der zweite Nutzer da ist

Toast, Protokoll-Andockfenster, Leerzustand, Schriftauswahl. Alle vier stehen
heute in jira-timesheet-qt, drei davon in ähnlicher Form auch in SiteHammer -
sie wandern mit dem Umbau der jeweiligen Stelle, nicht auf Vorrat.


---

## Was daraus geworden ist (23.08.2026)

| | vorher | nachher |
| --- | --- | --- |
| QAppFramework | 518 Zeilen, 3 Bausteine | rund 1900 Zeilen, 7 Bausteine, 82 Tests |
| jira-timesheet-qt: `ui/theme.py` | 774 | 160 |
| jira-timesheet-qt: Info-Dialog | 184 | 35 |
| jira-timesheet-qt: Haftungshinweis | 190 | 33 |
| jira-timesheet-qt: Einstellungen | 1239 | 1006 |
| SiteHammer: Info, Einstellungen, Umschalter | fehlten | aus der Bibliothek |

1153 Zeilen weniger in jira-timesheet-qt, und sie stehen nicht mehr doppelt.

### Befunde, die beim Bauen aufgefallen sind

- **Der Info-Dialog schnitt das laengste Zitat ab** (43 statt 73 Bildpunkte).
  Ein QLabel mit Wortumbruch meldet als Wunschgroesse eine Zeile;
  setSizePolicy(heightForWidth), adjustSize und alle drei
  Groessenbeschraenkungen des Layouts aendern nichts. Wirksam ist ein
  Nachschlag im showEvent, sobald die Breite feststeht.
- **Der Haftungshinweis wohnte hier, seine Stylesheet-Regeln nicht.** Derselbe
  Dialog sah in jeder Anwendung anders aus.
- **`#EmptyCard` war ungestylt** - SiteHammer setzt den Namen, eine Regel gab
  es nie.
- **grab() taugt nicht fuer Bildvergleiche**: wo das Widget nichts malt, ist
  die Pixmap uninitialisiert, zwei Aufnahmen desselben Widgets unterscheiden
  sich zuverlaessig.
- **toImage().constBits() liest freigegebenen Speicher.** Das Bild braucht eine
  eigene Variable, sonst wechseln die ersten Bytes von Aufruf zu Aufruf und ein
  Test faellt in zwei von zehn Laeufen.
- **Eine Anwendung braucht `skaliere()`**: ihre eigenen Regeln muessen durch
  dieselbe Zoom-Skalierung wie die der Bibliothek, sonst bleiben genau die auf
  fester Groesse.

### Nachgezogen am 23.08.2026 (0.10.0)

Die beiden Luecken sind geschlossen. `absturz` und `zelle` liegen jetzt hier,
jira-timesheet-qt spart weitere 255 Zeilen, SiteHammer hat beides zum ersten
Mal - vorher endete dort eine unbehandelte Ausnahme wortlos, und in allen vier
Tabellen klebte der Zelltext an der Spaltenkante.

Zwei Dinge sind beim Umzug allgemeiner geworden: der Fehlerbericht bekommt Name
und Version als Argument statt sie zu importieren, und optional eine Ablage
(`mitschreiben`), die den Absturz ueberlebt.

Ein Befund aus dem Umbau: ein Test in jira-timesheet-qt patchte
`crash_guard.ErrorDialog`, um den modalen Dialog fernzuhalten. Nach dem Umzug
greift das ins Leere - die Bibliothek baut ihren eigenen Dialog, und der Test
blockierte im echten. Wer einen Baustein herausloest, muss auch pruefen, wo
seine Tests hingreifen.

### Wenn der zweite Nutzer da ist

Toast, Protokoll-Andockfenster, Leerzustand, Schriftauswahl. Sie wandern mit
dem Umbau der jeweiligen Stelle, nicht auf Vorrat.
