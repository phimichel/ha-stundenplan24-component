# Stundenplan24 Integration für Home Assistant

[![GitHub Release](https://img.shields.io/github/release/phimichel/ha-stundenplan24-component.svg?style=flat-square)](https://github.com/phimichel/ha-stundenplan24-component/releases)
[![License](https://img.shields.io/github/license/phimichel/ha-stundenplan24-component.svg?style=flat-square)](LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/custom-components/hacs)

Eine Custom Component für Home Assistant zur Integration von Stundenplan- und Vertretungsplan-Daten von [stundenplan24.de](https://stundenplan24.de).

> **Status:** 🚧 In Entwicklung - Noch nicht für den produktiven Einsatz geeignet!

## 🎯 Features

### Aktuell implementiert
- ⏳ *Noch in Entwicklung*

### Geplant für v1.0
- 📚 **Stundenplan-Anzeige** - Übersicht über den aktuellen Stundenplan
- 📝 **Vertretungsplan** - Aktuelle Vertretungen für heute und morgen
- 🕐 **Aktuelle Stunde** - Sensor für die aktuell laufende Schulstunde
- ⏭️ **Nächste Stunde** - Vorschau auf die nächste Stunde
- 📅 **Tagesübersicht** - Kompletter Stundenplan für den Tag
- 🔄 **Automatische Updates** - Regelmäßige Aktualisierung der Daten
- 🇩🇪 **Deutsche Lokalisierung** - Vollständig deutsche Benutzeroberfläche

### Geplant für v2.0
- 📅 **Kalender-Integration** - Stundenplan als Home Assistant Kalender
- 🔔 **Benachrichtigungen** - Automatische Benachrichtigungen bei Stundenplanänderungen
- 🎨 **Lovelace Card** - Ansprechende Darstellung im Dashboard

## 📋 Voraussetzungen

- Home Assistant 2024.1.0 oder neuer
- Zugang zu einer stundenplan24.de Instanz (z.B. über die Schule)
- Python 3.9 oder neuer

## 🚀 Installation

### Via HACS (empfohlen)

> ⚠️ **Noch nicht verfügbar** - Die Integration ist noch nicht im HACS Default Repository

1. Öffne HACS in deiner Home Assistant Instanz
2. Klicke auf "Integrations"
3. Klicke auf das Menü oben rechts und wähle "Custom repositories"
4. Füge `https://github.com/phimichel/ha-stundenplan24-component` als Repository hinzu
5. Kategorie: Integration
6. Suche nach "Stundenplan24" und installiere es
7. Starte Home Assistant neu

### Manuelle Installation

1. Kopiere den Ordner `custom_components/stundenplan24` in dein Home Assistant `config/custom_components/` Verzeichnis
2. Starte Home Assistant neu

## ⚙️ Konfiguration

### Via UI (empfohlen)

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Klicke auf **+ Integration hinzufügen**
3. Suche nach **Stundenplan24**
4. Folge den Anweisungen zur Eingabe deiner Zugangsdaten

### Konfigurationsparameter

Die folgenden Informationen werden während der Einrichtung benötigt:

- **URL**: Die URL deiner stundenplan24.de Instanz (z.B. `https://schule.stundenplan24.de`)
- **Benutzername**: Dein Benutzername für den Zugang
- **Passwort**: Dein Passwort

### Optionale Einstellungen

Nach der Einrichtung können folgende Optionen angepasst werden:

- **Update-Intervall**: Wie oft die Daten aktualisiert werden (Standard: 30 Minuten)
- **Schüler-ID**: ID des Schülers (falls mehrere Schüler verwaltet werden)

## 📊 Entities

Die Integration erstellt folgende Entities:

### Sensoren

| Entity ID | Name | Beschreibung |
|-----------|------|--------------|
| `sensor.stundenplan24_aktuelle_stunde` | Aktuelle Stunde | Zeigt die aktuell laufende Schulstunde |
| `sensor.stundenplan24_naechste_stunde` | Nächste Stunde | Zeigt die nächste Schulstunde |
| `sensor.stundenplan24_vertretungen_heute` | Vertretungen Heute | Vertretungsplan für heute |
| `sensor.stundenplan24_vertretungen_morgen` | Vertretungen Morgen | Vertretungsplan für morgen |
| `sensor.stundenplan24_tagesplan` | Tagesplan | Kompletter Stundenplan für heute |

### Attribute

Jeder Sensor bietet zusätzliche Informationen als Attribute:

**Aktuelle/Nächste Stunde:**
- Fach
- Lehrer
- Raum
- Zeitraum (von - bis)
- Stundentyp (normal, Vertretung, Ausfall)

**Vertretungen:**
- Liste aller Vertretungen
- Betroffene Stunden
- Original-Lehrer / Vertretungs-Lehrer
- Änderungen (Raum, Fach, etc.)
- Bemerkungen

## 🔧 Entwicklung

Diese Integration wird mit einem Dev Container entwickelt. Siehe [CLAUDE.md](CLAUDE.md) und [PROJECT_PLAN.md](PROJECT_PLAN.md) für Details.

### Dev Container Setup

```bash
# Repository klonen
git clone git@github.com:phimichel/ha-stundenplan24-component.git
cd ha-stundenplan24-component

# Dev Container starten (in VS Code)
# - Installiere die "Dev Containers" Extension
# - Öffne Command Palette: "Dev Containers: Reopen in Container"
```

### Tests ausführen

```bash
# Unit Tests
pytest

# Integration Tests
pytest tests/integration/

# Mit Coverage
pytest --cov=custom_components.stundenplan24
```

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue für Bugs und Feature-Requests.

## 📝 Lizenz

Dieses Projekt steht unter der MIT Lizenz - siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- [stundenplan24-wrapper](https://github.com/phimichel/stundenplan24-wrapper) - Python Wrapper für die stundenplan24.de API
- Home Assistant Community für die exzellente Dokumentation

## 🔗 Links

- [Home Assistant](https://www.home-assistant.io/)
- [HACS](https://hacs.xyz/)
- [stundenplan24.de](https://stundenplan24.de)
- [Entwickler-Dokumentation](https://developers.home-assistant.io/)

## ⚠️ Disclaimer

Dies ist ein inoffizielles Projekt und steht in keiner Verbindung zu stundenplan24.de oder Indiware GmbH.
