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

## Anwendung der Patches

### Git Patch (Komplettversion)
```bash
cd stundenplan24-wrapper/
git apply /path/to/0001-cache-pytz-timezone-to-avoid-blocking-io.patch
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
