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
| `sensor.stundenplan24_vertretungen_heute` | Vertretungen Heute | Anzahl Vertretungen für heute |
| `sensor.stundenplan24_vertretungen_morgen` | Vertretungen Morgen | Anzahl Vertretungen für morgen |
| `sensor.stundenplan24_naechste_stunde` | Nächste Stunde | Die nächste anstehende Schulstunde |
| `sensor.stundenplan24_zusatzinformationen` | Zusatzinformationen | Wichtige Schulinformationen (ZusatzInfo) |

### Kalender

| Entity ID | Name | Beschreibung |
|-----------|------|--------------|
| `calendar.stundenplan24_wochenplan` | Wochenplan | Stundenplan als Kalender mit allen Stunden und ZusatzInfo |

### Sensor-Attribute

**sensor.stundenplan24_vertretungen_heute/morgen:**
- `substitutions`: Liste aller Vertretungen
- `date`: Datum des Plans
- `last_update`: Letzte Aktualisierung
- `absent_teachers`: Abwesende Lehrer
- `absent_forms`: Abwesende Klassen
- `additional_info`: Zusatzinformationen

**sensor.stundenplan24_naechste_stunde:**
- `period`: Stundennummer
- `start_time`: Startzeit
- `end_time`: Endzeit
- `teacher`: Lehrer
- `room`: Raum
- `course`: Kurs (falls vorhanden)
- `info`: Zusätzliche Informationen

**sensor.stundenplan24_zusatzinformationen:**
- `today`: Text mit allen Informationen für heute
- `today_lines`: Array mit einzelnen Zeilen für heute
- `today_date`: Datum für heute
- `tomorrow`: Text mit allen Informationen für morgen
- `tomorrow_lines`: Array mit einzelnen Zeilen für morgen
- `tomorrow_date`: Datum für morgen

## 🎨 Dashboard-Beispiele

### ZusatzInfo als Markdown Card (Empfohlen)

Die schönste Darstellung für Schulinformationen:

```yaml
type: markdown
title: Schulinformationen
content: |
  {% if state_attr('sensor.stundenplan24_zusatzinformationen', 'today') %}
  ## 📅 Heute ({{ state_attr('sensor.stundenplan24_zusatzinformationen', 'today_date') }})
  {{ state_attr('sensor.stundenplan24_zusatzinformationen', 'today') }}
  {% endif %}

  {% if state_attr('sensor.stundenplan24_zusatzinformationen', 'tomorrow') %}
  ## 📅 Morgen ({{ state_attr('sensor.stundenplan24_zusatzinformationen', 'tomorrow_date') }})
  {{ state_attr('sensor.stundenplan24_zusatzinformationen', 'tomorrow') }}
  {% endif %}

  {% if states('sensor.stundenplan24_zusatzinformationen') == 'Keine Informationen' %}
  ℹ️ Keine besonderen Informationen
  {% endif %}
```

### Kompakte Entities Card

```yaml
type: entities
title: Zusatzinformationen
entities:
  - entity: sensor.stundenplan24_zusatzinformationen
    name: Status
    icon: mdi:information-outline
  - type: attribute
    entity: sensor.stundenplan24_zusatzinformationen
    attribute: today
    name: Heute
  - type: attribute
    entity: sensor.stundenplan24_zusatzinformationen
    attribute: tomorrow
    name: Morgen
```

### Conditional Card (Nur bei wichtigen Infos)

Zeigt die Card nur an, wenn tatsächlich Informationen vorhanden sind:

```yaml
type: conditional
conditions:
  - condition: state
    entity: sensor.stundenplan24_zusatzinformationen
    state_not: "Keine Informationen"
card:
  type: markdown
  title: ⚠️ Wichtige Schulinformationen
  content: |
    {% if state_attr('sensor.stundenplan24_zusatzinformationen', 'today') %}
    **Heute:**
    {{ state_attr('sensor.stundenplan24_zusatzinformationen', 'today') }}
    {% endif %}

    {% if state_attr('sensor.stundenplan24_zusatzinformationen', 'tomorrow') %}
    **Morgen:**
    {{ state_attr('sensor.stundenplan24_zusatzinformationen', 'tomorrow') }}
    {% endif %}
```

### Vertikale Stack Card (Alles zusammen)

```yaml
type: vertical-stack
cards:
  - type: markdown
    title: 🏫 Stundenplan24 Informationen
    content: |
      **Status:** {{ states('sensor.stundenplan24_zusatzinformationen') }}

  - type: conditional
    conditions:
      - condition: state
        entity: sensor.stundenplan24_zusatzinformationen
        attribute: today
        state_not: null
    card:
      type: markdown
      title: 📅 Heute
      content: "{{ state_attr('sensor.stundenplan24_zusatzinformationen', 'today') }}"

  - type: conditional
    conditions:
      - condition: state
        entity: sensor.stundenplan24_zusatzinformationen
        attribute: tomorrow
        state_not: null
    card:
      type: markdown
      title: 📅 Morgen
      content: "{{ state_attr('sensor.stundenplan24_zusatzinformationen', 'tomorrow') }}"
```

### Custom Button Card (fortgeschritten)

Benötigt die [button-card](https://github.com/custom-cards/button-card) Custom Card:

```yaml
type: custom:button-card
entity: sensor.stundenplan24_zusatzinformationen
name: Schulinformationen
icon: mdi:school
show_state: true
show_label: true
label: |
  [[[
    const today = states['sensor.stundenplan24_zusatzinformationen'].attributes.today;
    const tomorrow = states['sensor.stundenplan24_zusatzinformationen'].attributes.tomorrow;
    let text = '';
    if (today) text += '📅 Heute: ' + today.split('\n')[0];
    if (tomorrow) text += '\n📅 Morgen: ' + tomorrow.split('\n')[0];
    return text || 'Keine Informationen';
  ]]]
styles:
  card:
    - height: auto
  label:
    - text-align: left
    - white-space: pre-wrap
tap_action:
  action: more-info
```

## 🔔 Automatisierungen

### Benachrichtigung bei neuen Schulinfos

```yaml
automation:
  - alias: "Schulinfo Benachrichtigung"
    description: "Benachrichtigt bei neuen Zusatzinformationen"
    trigger:
      - platform: state
        entity_id: sensor.stundenplan24_zusatzinformationen
        attribute: today
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.stundenplan24_zusatzinformationen', 'today') != None }}"
    action:
      - service: notify.mobile_app_dein_handy
        data:
          title: "📚 Schulinfo heute"
          message: |
            {{ state_attr('sensor.stundenplan24_zusatzinformationen', 'today') }}
```

### Morgendliche Zusammenfassung

```yaml
automation:
  - alias: "Morgendliche Schulinfo"
    description: "Sendet jeden Morgen die Infos für heute"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: sensor.stundenplan24_zusatzinformationen
        attribute: today
        state_not: null
    action:
      - service: notify.family
        data:
          title: "Guten Morgen! 🌅"
          message: |
            Schulinfos für heute:
            {{ state_attr('sensor.stundenplan24_zusatzinformationen', 'today') }}
```

## 🔧 Entwicklung

Diese Integration wird mit einem Dev Container entwickelt. Siehe [CLAUDE.md](CLAUDE.md) und [PROJECT_PLAN.md](PROJECT_PLAN.md) für Details.

### Voraussetzungen

- Docker Desktop
- Visual Studio Code
- VS Code Extension: "Dev Containers" (ms-vscode-remote.remote-containers)

### Dev Container Setup

```bash
# Repository klonen
git clone git@github.com:phimichel/ha-stundenplan24-component.git
cd ha-stundenplan24-component

# In VS Code öffnen
code .

# Dev Container starten
# 1. VS Code Command Palette öffnen (Cmd/Ctrl + Shift + P)
# 2. "Dev Containers: Reopen in Container" ausführen
# 3. Warten bis Container gebuildet ist
```

Der Dev Container startet automatisch:
- **Python Development Container** - Für Code-Entwicklung mit allen notwendigen Tools
- **Home Assistant Container** - Läuft auf Port 8123 für Testing

### Entwicklungs-Workflow

1. **Änderungen an der Integration vornehmen**
   - Dateien in `custom_components/stundenplan24/` bearbeiten
   - Änderungen werden automatisch in den HA Container gemountet

2. **Home Assistant neu laden**
   - Im Browser: http://localhost:8123
   - Entwicklertools → YAML → "Alle YAML-Konfigurationen neu laden"
   - Oder: Home Assistant Container neu starten

3. **Integration testen**
   - Einstellungen → Geräte & Dienste → Integration hinzufügen
   - "Stundenplan24" suchen und konfigurieren

4. **Logs prüfen**
   ```bash
   # Im Dev Container Terminal
   docker logs ha-stundenplan24-dev -f
   ```

### Projektstruktur

```
.
├── .devcontainer/
│   ├── devcontainer.json      # Dev Container Konfiguration
│   └── docker-compose.yml     # Docker Services (HA + Dev)
├── config/
│   └── configuration.yaml     # Home Assistant Config
├── custom_components/
│   └── stundenplan24/         # Die Integration
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── const.py
│       ├── sensor.py
│       ├── strings.json
│       └── translations/
│           └── de.json
├── requirements-dev.txt       # Python Dependencies
└── README.md
```

### Tests ausführen

```bash
# Unit Tests (noch nicht implementiert)
pytest

# Integration Tests
pytest tests/integration/

# Mit Coverage
pytest --cov=custom_components.stundenplan24

# Linting
ruff check .
black --check .
```

### Debugging

VS Code ist bereits für Debugging konfiguriert:
- Setze Breakpoints in Python-Dateien
- Drücke F5 oder nutze das Debug Panel
- Der Debugger verbindet sich mit Home Assistant

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
