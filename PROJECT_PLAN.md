# Stundenplan24 Home Assistant Integration - Projektplan

## 🎯 Projektziel
Entwicklung einer Custom Component für Home Assistant zur Anzeige von Stundenplan- und Vertretungsplan-Daten von stundenplan24.de mit Fokus auf Schüler-Ansichten.

## 📦 Externe Dependencies
- **stundenplan24-wrapper Library**: https://github.com/phimichel/stundenplan24-wrapper
  - Python 3.9+ kompatibel
  - Bietet Zugriff auf 12+ API-Endpoints
  - Automatisches Löschen von Plänen älter als 10 Tage
  - Nur bei Bedarf erweitern (Library soll HA-unabhängig bleiben)

## 🎓 Fokus: Schüler-Ansichten
**Primäre Ansichten (Priorität):**
- ✅ Indiware Mobil (Student)
- ✅ Vertretungsplan (Student)
- ✅ Wochenplan
- ✅ Stundenplan

**Lehrer-Ansichten:**
- ⏸️ Vorerst zurückgestellt

## 📋 Entwicklungsplan

### Phase 1: Infrastruktur & Setup ✅
- [x] Git Repository initialisiert
- [x] Remote Repository verbunden
- [ ] Dev Container einrichten
  - `.devcontainer/devcontainer.json` erstellen
  - `docker-compose.yml` mit Home Assistant Container
  - Volume Mounts für `custom_components/stundenplan24`
  - Configuration für schnelles Testing

- [ ] Projektstruktur anlegen
  ```
  custom_components/stundenplan24/
  ├── __init__.py              # Integration Setup
  ├── manifest.json            # Component Metadata (PFLICHT)
  ├── config_flow.py           # UI Configuration
  ├── coordinator.py           # Data Update Coordinator
  ├── sensor.py               # Sensor Entities
  ├── const.py                # Constants
  ├── strings.json            # Config Flow Strings (PFLICHT für config_flow)
  └── translations/
      └── de.json             # Deutsche Übersetzungen
  ```

### Phase 2: Grundlegende Integration
- [ ] **manifest.json definieren**
  - Domain: `stundenplan24`
  - Dependencies: `stundenplan24-wrapper`
  - Version
  - Integration Metadata (name, documentation, issue_tracker)
  - Requirements

- [ ] **const.py - Konstanten**
  - DOMAIN = "stundenplan24"
  - Config Keys
  - Update Intervals (Standard: 30 Minuten)
  - Sensor Types

- [ ] **config_flow.py - Konfiguration**
  - User Input für stundenplan24 URL/Credentials
  - Validation der Zugangsdaten via stundenplan24-wrapper
  - Options Flow für zusätzliche Einstellungen
  - Async/Await Pattern

### Phase 3: Daten-Management
- [ ] **coordinator.py - Update Coordinator**
  - DataUpdateCoordinator Implementation
  - API Calls zur stundenplan24-wrapper Library
  - Error Handling & Retry Logic
  - Caching & Update-Logik
  - Async Pattern

- [ ] **__init__.py - Integration Setup**
  - async_setup_entry
  - async_unload_entry
  - Coordinator Initialisierung
  - Platform Setup (sensor)

### Phase 4: Sensor Entities
- [ ] **sensor.py - Sensor Entities**
  - **Sensor-Typen:**
    - Aktuelle Stunde
    - Nächste Stunde
    - Tagesplan (heute)
    - Vertretungen heute
    - Vertretungen morgen
  - Attributes mit detaillierten Informationen
  - Device Info für Gruppierung
  - State Class & Device Class
  - Unique IDs

### Phase 5: Lokalisierung & Polish
- [ ] **Übersetzungen**
  - `strings.json` für Config Flow (EN)
  - `translations/de.json` für deutsche UI
  - Error Messages

- [ ] **Dokumentation**
  - README.md mit Installation & Setup
  - Beispiel-Konfigurationen
  - Screenshots
  - Troubleshooting Guide

### Phase 6: Testing & Qualität
- [ ] **Tests schreiben**
  - Unit Tests für Coordinator
  - Config Flow Tests
  - Mock für stundenplan24 API

- [ ] **Code Quality**
  - HACS Compliance prüfen
  - Home Assistant Coding Standards
  - Type Hints überall
  - Docstrings

## 🚀 Geplante Features (TODO für später)

### Kalender-Integration 📅
- [ ] Calendar Platform implementieren
- [ ] Stundenplan als Kalender-Events
- [ ] Vertretungen als separate Events
- [ ] iCal Export

### Notifications 🔔
- [ ] Service für Notification bei Stundenplanänderungen
- [ ] Persistent Notification bei neuen Vertretungen
- [ ] Configurable Notification Trigger
- [ ] Mobile App Integration

### Lovelace Card 🎨
- [ ] Custom Card für schöne Darstellung
- [ ] Stundenplan-Übersicht
- [ ] Vertretungsplan-Widget
- [ ] Responsive Design
- [ ] Themes Support

## 🔑 Design-Entscheidungen

### Sensor-Strategie
**Gewählter Ansatz:** Kombination
- Ein zentraler Coordinator für API-Calls
- Mehrere spezialisierte Sensoren für verschiedene Ansichten
- Shared Data über Coordinator
- Jeder Sensor entscheidet, welche Daten er anzeigt

**Vorteile:**
- Effizient: Ein API Call für alle Sensoren
- Flexibel: Sensoren einzeln in Automationen nutzbar
- Übersichtlich: Klare Trennung der Daten

### Daten-Refresh
- **Standard:** 30 Minuten
- **Konfigurierbar:** Über Options Flow
- **Manuell:** Service Call `homeassistant.update_entity`
- **Smart:** Höhere Frequenz während Schulzeiten (optional)

### Multi-User Support
- Ein Config Entry pro Schüler
- Eindeutige Device IDs per Schüler
- Shared Coordinator möglich bei gleicher Schule/Klasse
- Spätere Erweiterung für Familien

## ✅ Testumgebung
- Testzugang zu stundenplan24 vorhanden
- Dev Container für isoliertes Testing
- Lokale Home Assistant Instanz

## 🛠️ Technologie-Stack
- **Sprache:** Python 3.9+
- **Framework:** Home Assistant Core
- **API Wrapper:** stundenplan24-wrapper
- **Testing:** pytest, pytest-homeassistant-custom-component
- **Dev Environment:** Docker, Dev Containers

## 📝 Namenskonventionen
- **Domain:** `stundenplan24` (lowercase, snake_case)
- **Dateien:** lowercase, snake_case
- **Klassen:** PascalCase
- **Funktionen/Variablen:** snake_case
- **Konstanten:** UPPERCASE_SNAKE_CASE

## 🔗 Wichtige Links
- GitHub Repository: https://github.com/phimichel/ha-stundenplan24-component
- stundenplan24-wrapper: https://github.com/phimichel/stundenplan24-wrapper
- Home Assistant Developer Docs: https://developers.home-assistant.io/
- Creating Integration: https://developers.home-assistant.io/docs/creating_component_index

## 📅 Meilensteine

### v0.1.0 - MVP (Minimum Viable Product)
- Grundlegende Integration
- Config Flow
- Ein Sensor (z.B. nächste Stunde)
- Testbar im Dev Container

### v0.2.0 - Feature Complete
- Alle geplanten Sensoren
- Deutsche Übersetzungen
- Dokumentation

### v0.3.0 - Production Ready
- Tests
- Error Handling
- HACS Ready

### v1.0.0 - First Release
- Stabil
- Vollständige Dokumentation
- Community Feedback eingearbeitet

### v2.0.0 - Extended Features
- Kalender-Integration
- Notifications
- Lovelace Card

## 🎯 Aktueller Status
**Phase:** Setup & Planung ✅
**Nächster Schritt:** Dev Container & Basis-Struktur erstellen
