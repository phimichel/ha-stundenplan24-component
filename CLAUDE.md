# Home Assistant Stundenplan24 Integration - Entwicklungsdokumentation

## Projektziel
Entwicklung einer Custom Component für Home Assistant zur Anzeige von Stundenplan- und Vertretungsplan-Daten von stundenplan24.de.

## Wichtige Informationen

### Externe Dependencies
- **stundenplan24-wrapper Library**: https://github.com/phimichel/stundenplan24-wrapper
  - Python 3.9+ kompatibel
  - Bietet Zugriff auf 12+ API-Endpoints
  - Unterstützt Schüler- und Lehreransichten
  - Automatisches Löschen von Plänen älter als 10 Tage
  - Status: "probably not complete" - eventuell Erweiterungen nötig

### Dependency Vendoring (Temporär)

**Status:** Aktuell sind die Dependencies lokal vendored, da sie noch nicht auf PyPI veröffentlicht sind.

**Vendored Packages:**
- `custom_components/stundenplan24/stundenplan24_py/` - stundenplan24-wrapper
- `custom_components/stundenplan24/pipifax_proxy_manager/` - Proxy Manager Dependency
- `custom_components/stundenplan24/pipifax_io/` - I/O Utilities Dependency

**Externe Dependencies in manifest.json:**
- pytz~=2025.2
- curl_cffi
- urllib3[socks]
- psutil
- bson

**TODO:** Sobald stundenplan24-wrapper auf PyPI veröffentlicht ist:
1. Vendored code entfernen
2. `manifest.json` requirements updaten zu: `["stundenplan24-wrapper>=x.y.z"]`
3. Imports anpassen von `.stundenplan24_py` zu `stundenplan24_py`

### Verfügbare Ansichten
**Schüler:**
- Indiware Mobil (Student)
- Vertretungsplan (Student)
- Wochenplan
- Stundenplan

**Lehrer:**
- Indiware Mobil (Teacher)
- Vertretungsplan (Teacher)

## Technische Anforderungen

### Home Assistant Component
- Muss Home Assistant Coding Standards folgen
- Config Flow für UI-basierte Konfiguration
- Sensor Entities für Stundenplan-Daten
- Options Flow für zusätzliche Konfiguration
- Proper async/await Pattern
- Koordinator für API-Calls (UpdateCoordinator)

### Dev Container Setup
- Home Assistant Container für Testing
- Volume Mounts für Custom Component
- Konfiguration für schnelles Reload

### stundenplan24-wrapper Library
- **Nur Homeassistant-unabhängige Funktionalität**
- Reine Python API Wrapper
- Keine HA-spezifischen Imports
- Bei Bedarf erweitern/anpassen

## Datenschema
Zu klären:
- Welche Daten werden von der API bereitgestellt?
- Welche Attribute sollen in den Sensoren verfügbar sein?
- Refresh-Intervalle

## Offene Fragen
1. Welche stundenplan24 Instanz(en) soll getestet werden?
2. Gibt es Test-Zugangsdaten?
3. Sollen mehrere Schüler/Lehrer gleichzeitig unterstützt werden?
4. Welche Sensor-Typen sind gewünscht? (z.B. nächste Stunde, Tagesplan, Vertretungen)
5. Benachrichtigungen bei Stundenplanänderungen?
6. Kalender-Integration?

## Projekt-Struktur
```
stundenplan24/
├── custom_components/
│   └── stundenplan24/
│       ├── __init__.py                 # Integration Setup
│       ├── manifest.json               # Component Metadata
│       ├── config_flow.py              # UI Configuration
│       ├── coordinator.py              # Data Update Coordinator
│       ├── sensor.py                   # Sensor Entities
│       ├── const.py                    # Constants
│       ├── strings.json                # Translations
│       ├── stundenplan24_py/           # Vendored: stundenplan24-wrapper
│       ├── pipifax_proxy_manager/      # Vendored: Proxy Manager
│       └── pipifax_io/                 # Vendored: I/O Utilities
├── .devcontainer/
│   ├── devcontainer.json               # Dev Container Config
│   └── docker-compose.yml              # HA Container Setup
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # Test Fixtures
│   ├── test_config_flow.py             # Config Flow Tests
│   ├── test_coordinator.py             # Coordinator Tests
│   └── test_init.py                    # Integration Setup Tests
├── .venv/                              # Virtual Environment (local only)
├── pytest.ini                          # Pytest Configuration
├── requirements-dev.txt                # Development Dependencies
└── README.md                           # Dokumentation
```

## Entwicklungs-Workflow
1. Dev Container starten
2. Custom Component entwickeln
3. In HA Container testen
4. Iterativ verbessern
5. Tests schreiben
6. Dokumentation aktualisieren

## Git Konventionen

### Commit Messages
- **KEINE Claude/Claude Code Referenzen** in Commit-Nachrichten
- Klare, beschreibende Commit-Nachrichten in Englisch
- Format: `<type>: <kurze Beschreibung>` gefolgt von optionalem Body
- Types: feat, fix, docs, style, refactor, test, chore
- Beispiel:
  ```
  feat: Add config flow for initial setup

  - Implement async_step_user for credential input
  - Add validation for stundenplan24 API
  - Handle connection errors gracefully
  ```

### Branch Strategy
- `main`: Stable releases
- `dev`: Development branch
- Feature branches: `feature/<feature-name>`
- Bugfix branches: `fix/<bug-description>`

## Nützliche Links
- Home Assistant Developer Docs: https://developers.home-assistant.io/
- Custom Integration Tutorial: https://developers.home-assistant.io/docs/creating_component_index
- Config Flow Docs: https://developers.home-assistant.io/docs/config_entries_config_flow_handler
- Example for customer sensor: https://github.com/home-assistant/example-custom-config/tree/master/custom_components/example_sensor
