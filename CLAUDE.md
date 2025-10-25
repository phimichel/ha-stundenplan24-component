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

**Upstream Patches:**
Patches für stundenplan24-wrapper befinden sich im `patches/` Verzeichnis:
- `0001-cache-pytz-timezone-to-avoid-blocking-io.patch` - Behebt Home Assistant Warnung über blockierendes I/O in Event Loop
- Siehe `patches/README.md` für Details und Anwendungshinweise

**TODO:** Sobald stundenplan24-wrapper auf PyPI veröffentlicht ist:
1. Patches upstream einreichen
2. Vendored code entfernen
3. `manifest.json` requirements updaten zu: `["stundenplan24-wrapper>=x.y.z"]`
4. Imports anpassen von `.stundenplan24_py` zu `stundenplan24_py`

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

---

## Aktueller Entwicklungsstand (Session vom 25.10.2025)

### ✅ Implementierte Features

#### 1. Options Flow - Klassenauswahl
**Status:** Vollständig implementiert und getestet
**Commit:** `d488767` - "feat: Add form selection and timetable parsing"

- Benutzer kann nach initialer Konfiguration seine Klasse/Form auswählen (z.B. "5a", "10b")
- UI zeigt Dropdown mit verfügbaren Klassen aus der API
- Validierung der API-Verbindung beim Laden der Klassen
- Fehlerbehandlung für fehlende form_plan_client und Connection-Fehler
- **Tests:** 4 Tests (init, selection, no_form_client, connection_error)

**Dateien:**
- `custom_components/stundenplan24/config_flow.py` - OptionsFlow Klasse hinzugefügt
- `custom_components/stundenplan24/const.py` - CONF_FORM Konstante
- `tests/test_config_flow.py` - 4 neue Tests

#### 2. Coordinator - IndiwareMobil Datenverarbeitung
**Status:** Vollständig implementiert und getestet
**Commit:** `d488767` - "feat: Add form selection and timetable parsing"

- Parst XML-Response von IndiwareMobil API zu strukturierten IndiwareMobilPlan Objekten
- Filtert Stundenplan automatisch nach ausgewählter Klasse aus Options
- Unterstützt korrektes deutsches Datumsformat ("Samstag, 25. Januar 2025")
- **Tests:** 2 neue Tests (parse XML, filter by form)

**Dateien:**
- `custom_components/stundenplan24/coordinator.py` - XML-Parsing und Form-Filterung
- `tests/test_coordinator.py` - 2 neue Tests mit vollständigen XML-Fixtures
- `tests/conftest.py` - mock_indiware_mobil_plan Fixture

#### 3. Calendar Platform - Wochenplan-Anzeige
**Status:** Vollständig implementiert und getestet
**Commit:** `d95c194` - "feat: Add calendar platform for weekly timetable display"

- Zeigt Stundenplan als native Home Assistant Calendar Events
- Projiziert Stunden auf aktuelle Woche (wiederholend)
- Events enthalten: Fach (Summary), Lehrer, Raum (Description)
- Timezone-aware Datetimes für HA-Kompatibilität
- Unterstützt Date-Range-Filtering für Calendar-View
- **Tests:** 5 Tests (setup, events, attributes, no_timetable, date_filtering)

**Dateien:**
- `custom_components/stundenplan24/calendar.py` - NEU: CalendarEntity Implementierung
- `custom_components/stundenplan24/__init__.py` - Platform.CALENDAR registriert
- `custom_components/stundenplan24/sensor.py` - Dict storage compatibility
- `tests/test_calendar.py` - NEU: 5 umfassende Tests
- `tests/conftest.py` - mock_timetable_with_lessons Fixture
- `tests/test_init.py` - Coordinator extraction fix

**Entity Name:** `calendar.stundenplan24_wochenplan`

### 📊 Test-Status
**26 von 26 Tests bestehen** ✅
- 11 Config Flow Tests (7 ursprünglich + 4 Options Flow)
- 7 Coordinator Tests (5 ursprünglich + 2 IndiwareMobil)
- 5 Calendar Tests (neu)
- 3 Init Tests

### 🔄 Technische Details

#### Datenstruktur
Die Integration speichert jetzt Daten in einem Dict-Format für Flexibilität:
```python
hass.data[DOMAIN][entry_id] = {
    "coordinator": coordinator,  # Stundenplan24Coordinator
    "calendar": calendar_entity  # Optional, von calendar.py gesetzt
}
```

**Backward Compatibility:** Alle Platforms (sensor, calendar) unterstützen beide Formate:
- Legacy: `hass.data[DOMAIN][entry_id]` = Coordinator direkt
- Neu: `hass.data[DOMAIN][entry_id]` = Dict mit `{"coordinator": ...}`

#### Calendar Event Projektion
- Lessons werden aus dem Timetable-XML extrahiert
- Jede Lesson wird auf die aktuelle Woche projiziert (wiederholend)
- Weekday-Mapping: `lesson.period % 5` (0=Monday, 4=Friday)
- Timezone-aware datetime via `dt_util.start_of_local_day()`

### 📝 Nächste Schritte für kommende Session

#### Optionale Features (nicht dringend)

1. **Sensor "Stundenplan Heute"** (für Dashboard Cards)
   - Native Value: Anzahl Stunden heute
   - Attributes: Liste der heutigen Stunden mit Details
   - Besser geeignet für Lovelace Cards als Calendar
   - **Aufwand:** ~2h (Test-first)

2. **Wochentags-Mapping verbessern**
   - Aktuell: `lesson.period % 5` (Approximation)
   - Besser: Tatsächliche Wochentags-Information aus XML nutzen
   - Erfordert Analyse der XML-Struktur für Day-Mapping
   - **Aufwand:** ~1h

3. **Translations (strings.json, de.json, en.json)**
   - Options Flow UI-Strings
   - Entity Names und Descriptions
   - Error Messages
   - **Aufwand:** ~30min

4. **README.md erstellen**
   - Installation Instructions
   - Configuration Guide
   - Screenshots
   - **Aufwand:** ~1h

### 🐛 Bekannte Issues / Verbesserungspotential

1. **Deprecation Warnings** (nicht kritisch)
   - Source: `stundenplan24_py/indiware_mobil.py` Zeilen 98, 112, 118, 134, 139
   - Issue: `for period in xml.find("KlStunden") or []:`
   - Fix: `elem = xml.find("KlStunden"); for period in (elem if elem is not None else []):`
   - **Note:** Betrifft vendored library, sollte upstream gefixt werden

2. **Wochentags-Zuordnung**
   - Aktuell: Alle Lessons werden über Mo-Fr verteilt (`period % 5`)
   - Real: Lessons haben spezifische Wochentage im XML
   - **Impact:** Niedrig für wöchentliche Pläne, aber nicht 100% akkurat

3. **Lesson Time Zones**
   - Aktuell: Nutzt System-Timezone (`dt_util.start_of_local_day`)
   - Könnte: Timezone aus HA Config nutzen
   - **Impact:** Sehr niedrig, nur bei abweichender System-TZ

### 🎯 Empfohlene Reihenfolge für nächste Session

1. **Sensor "Stundenplan Heute"** implementieren (falls gewünscht für Dashboard)
2. Translations hinzufügen (schnell, verbessert UX)
3. README.md mit Screenshots
4. Optional: Wochentags-Mapping verbessern
5. Optional: Deprecation Warnings fixen (upstream PR)
