# Patches for Upstream (stundenplan24-wrapper)

Diese Patches beheben Probleme in der vendored stundenplan24-wrapper Library und sollten upstream eingereicht werden.

## Verfügbare Patches

### 1. Cache pytz timezone to avoid blocking I/O in event loop

**Dateien:**
- `0001-cache-pytz-timezone-to-avoid-blocking-io.patch` - Kompletter Git Patch
- `indiware_mobil.patch` - Standalone patch für indiware_mobil.py
- `substitution_plan.patch` - Standalone patch für substitution_plan.py

**Problem:**
Home Assistant warnt vor blockierenden I/O-Aufrufen in der Event Loop:
```
WARNING (MainThread) [homeassistant.util.loop] Detected blocking call to open with args
(...) inside the event loop by custom integration 'stundenplan24' at
custom_components/stundenplan24/stundenplan24_py/indiware_mobil.py, line 43:
pytz.timezone("Europe/Berlin")
```

**Lösung:**
- Cache `pytz.timezone("Europe/Berlin")` beim Modul-Import als `_BERLIN_TZ`
- Ersetze alle `pytz.timezone("Europe/Berlin")` Aufrufe mit der gecachten Variable
- Blockierendes I/O passiert nur einmal beim Modul-Load, nicht während der Event Loop

**Betroffene Dateien:**
- `indiware_mobil.py`
- `substitution_plan.py`

### 2. Fix XML element truth value deprecation warnings

**Datei:**
- `0002-fix-xml-element-truth-value-deprecation.patch` - Kompletter Git Patch

**Problem:**
Python's XML ElementTree zeigt Deprecation-Warnungen bei direktem Truth-Value-Testing:
```
DeprecationWarning: Testing an element's truth value will raise an exception in future versions.
Use specific 'len(elem)' or 'elem is not None' test instead.
  for period in xml.find("KlStunden") or []:
```

**Lösung:**
- Ersetze `xml.find("tag") or []` mit `elem = xml.find("tag"); for item in (elem if elem is not None else []):`
- Explizite `is not None` Prüfung statt impliziten Truth-Value-Test
- Betrifft 5 Stellen in `Form.from_xml()`: KlStunden, Kurse, Unterricht, Klausuren, Aufsichten

**Betroffene Dateien:**
- `indiware_mobil.py` (Lines 100, 114, 120, 136, 141)

**Technischer Hintergrund:**
XML Elements in Python's ElementTree haben ein spezielles Truth-Value-Verhalten (empty element = False), welches deprecated wird. Die neue empfohlene Methode ist explizite Checks auf `is not None` oder `len(elem) > 0`.

## Anwendung der Patches

### Git Patches (Komplettversion)

**Patch 1 (pytz caching):**
```bash
cd stundenplan24-wrapper/
git apply /path/to/0001-cache-pytz-timezone-to-avoid-blocking-io.patch
```

**Patch 2 (XML deprecation fix):**
```bash
cd stundenplan24-wrapper/
git apply /path/to/0002-fix-xml-element-truth-value-deprecation.patch
```

### Standalone Patches
```bash
cd stundenplan24-wrapper/src/stundenplan24_py/
patch -p0 < /path/to/indiware_mobil.patch
patch -p0 < /path/to/substitution_plan.patch
```

## Upstream Repository

https://github.com/phimichel/stundenplan24-wrapper

## Verifikation

Nach Anwendung der Patches sollten alle Tests durchlaufen:
```bash
pytest
```

Die Warnung von Home Assistant sollte nicht mehr erscheinen.
