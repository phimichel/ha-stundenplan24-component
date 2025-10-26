# Testing Translations in Home Assistant

## Problem
Die Übersetzungen werden nicht angezeigt - es steht immer noch "form" statt "Klasse" im Dialog.

## Mögliche Ursachen

### 1. Translation Cache
Home Assistant cached Translations. Nach Änderungen an `strings.json` oder `translations/*.json`:

**Lösung:**
```bash
# Home Assistant neu starten
# ODER
# Integration entfernen und neu hinzufügen
# ODER
# Browser-Cache leeren (Strg+Shift+R / Cmd+Shift+R)
```

### 2. Entwicklermodus aktivieren
In der Home Assistant `configuration.yaml`:
```yaml
homeassistant:
  # Disable translation caching in dev mode
  # This forces HA to reload translations on every request
  customize: {}
```

### 3. Translation-Dateien überprüfen

**Prüfen ob Dateien geladen werden:**
1. Home Assistant Developer Tools → Logs
2. Nach "translation" suchen
3. Schauen ob Fehler beim Laden der Translations auftreten

### 4. Browser Developer Tools
1. F12 öffnen
2. Network Tab
3. Integration konfigurieren
4. Nach `translations` Request suchen
5. Response prüfen - enthält sie die deutschen Texte?

## Debugging Steps

### Schritt 1: Integration neu laden
```bash
# In Home Assistant:
# Einstellungen → Geräte & Dienste → Stundenplan24
# ... → Integration neu laden
```

### Schritt 2: Home Assistant komplett neu starten
```bash
# Einstellungen → System → Neu starten
```

### Schritt 3: Integration komplett entfernen und neu hinzufügen
```bash
# Einstellungen → Geräte & Dienste → Stundenplan24
# ... → Integration entfernen
# Dann neu hinzufügen
```

### Schritt 4: Browser Cache leeren
- Chrome/Edge: `Strg+Shift+R` (Windows) / `Cmd+Shift+R` (Mac)
- Firefox: `Strg+F5` (Windows) / `Cmd+Shift+R` (Mac)

### Schritt 5: Translations manuell prüfen
```bash
# Im HA Container / Core Installation:
cd /config/custom_components/stundenplan24
cat strings.json
cat translations/de.json

# Prüfen ob Dateien existieren und korrekt sind
```

## Erwartetes Verhalten

### Englisch (Browser Language: en)
- **Config Step 1 Title:** "Stundenplan24 Setup"
- **Config Step 2 Title:** "Class Selection"
- **Config Step 2 Field:** "Class"
- **Options Title:** "Subject Filter"
- **Options Field:** "Subjects to display"

### Deutsch (Browser Language: de)
- **Config Step 1 Title:** "Stundenplan24 Einrichtung"
- **Config Step 2 Title:** "Klassenauswahl"
- **Config Step 2 Field:** "Klasse"
- **Options Title:** "Fächerfilter"
- **Options Field:** "Anzuzeigende Fächer"

## Bekannte Home Assistant Verhaltensweisen

1. **Browser Language Detection:**
   - HA nutzt die Browser-Sprache (`navigator.language`)
   - Falls `de-DE` → lädt `translations/de.json`
   - Falls `en-US` → nutzt `strings.json` (Fallback)

2. **Translation Fallback:**
   - Wenn Key nicht in `de.json` → nutzt `strings.json`
   - Wenn Key nirgends → zeigt technischen Key (z.B. "form")

3. **Custom Component Translations:**
   - Werden NACH Core-Translations geladen
   - Überschreiben Core-Translations wenn gleicher Key

## Wenn nichts hilft

### Option A: Translations direkt im Code setzen (Workaround)
Statt auf automatische Translations zu vertrauen, könnten wir die Titel/Beschreibungen direkt im `config_flow.py` setzen:

```python
return self.async_show_form(
    step_id="select_form",
    data_schema=schema,
    errors=errors,
    description_placeholders={
        "title": "Klassenauswahl",
        "description": "Wählen Sie die Klasse aus..."
    }
)
```

### Option B: Home Assistant Core Issue
Wenn Translations grundsätzlich nicht funktionieren:
1. Home Assistant Version prüfen (mind. 2023.x empfohlen)
2. Logs nach Translation-Fehlern durchsuchen
3. GitHub Issue bei Home Assistant öffnen

## Testen in Development Environment

Im Dev Container (`.devcontainer`):
```bash
# HA Container neu starten
docker compose restart homeassistant

# Logs verfolgen
docker compose logs -f homeassistant | grep -i translation
```

## Verifizierung

Nach dem Neustart:
1. Browser Cache leeren
2. Zu Einstellungen → Geräte & Dienste navigieren
3. "Integration hinzufügen" → "Stundenplan24" suchen
4. **Schritt 2 sollte jetzt "Klassenauswahl" heißen (statt "form")**
