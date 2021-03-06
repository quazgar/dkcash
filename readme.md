# Direktkreditverwaltung mit einem Standalon-Programm und Gnucash-Backend

Ziel ist ein lokal laufendes Programm (kein Webservice) zur
Direktkreditverwaltung.  Als Backend soll eine GnuCash-Datenbank dienen, die
auch von GnuCash geöffnet und verarbeitet werden kann.

# Anforderungen
## Installation
- Einfach installierbar über `setup.py` oder `pip3 install`.  Eine
  Installationsanleitung befindet sich in `install.md`.
- Für Windows, Mac und (die üblichen) Linux(distributionen) existieren auch
  "Ein-Klick-Skripte" zur Installation.

## Export- und Reportoptionen
- Weiterbearbeitung der Darlehenskonten mit GnuCash.
- Export der Konten nach ods.
- Auflistung und Export nach nächsten Fälligkeiten.

# Überlegungen zur Implementierung
## GUI-Frontend
Qt als GUI-Toolkit über PyQt, wird auf allen üblichen Systemen unterstützt.

## Backend
- GnuCash-kompatible Sqlite-Datenbank, Zugriff über
  [piecash](https://github.com/sdementen/piecash).
- Piecash-Funktionen verwenden für:
  - Ein Unterkonto pro Kreditvertrag
  - Ein-/Auszahlungen, auch Zinsen, für jeden Kreditvertrag.
- Extra-Tabellen in Datenbank für:
  - Kreditgeber*innen: Name, Kontaktdaten, Einverständnis für Newsletter
  - Kreditverträge: Vertragsnummer, Datum, Laufzeitinformationen
  Details zum Datenbankschema sind in `db_schema.org` aufgeführt.

# Roadmap
Ideen, was als nächstes getan werden könnte:
- Detaillierte Liste in [doc/todo.md](doc/todo.md)
- Tests schreiben für Methoden in `dkdata.py` und `common.py` (auch noch nicht
  implementierte).
- Implementation der High-Level-Klassen und (einiger) Methoden in `common.py`.
- Implementation einer GUI, die die Klassen aus `common.py` verwendet.
  - Die von GUI benötigten Methoden in `common.py` implementieren, bei Bedarf
    auch neu- oder umdefinieren.

