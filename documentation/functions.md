# Tower Control – Funktionsdokumentation / Feature Documentation

## 🇩🇪 Deutsch

### Add-on `tower_control`

Das Add-on baut die nativen Host-Tools und stellt sie beim Start bereit.

**Wichtige Dateien:**
- `addons/tower_control/config.yaml`: Add-on-Metadaten, Optionen und Schema
- `addons/tower_control/run.sh`: Startlogik, Optionsübergabe, Binary-Deployment
- `addons/tower_control/tower_ledctl.c`: LED-Steuerung inkl. Effekte
- `addons/tower_control/tower_oledctl.c`: OLED-Textausgabe (1–3 Zeilen)
- `addons/tower_control/tower_fanctl.c`: Temperaturgesteuerter Lüfter-Daemon

**Ablauf beim Start:**
1. Add-on liest Optionen via `bashio::config` aus `config.yaml`.
2. Binaries werden nach `/share/tower_control/` kopiert (= `/mnt/data/supervisor/share/tower_control/` auf dem Host).
3. `tower_fanctl` wird als Hintergrund-Daemon gestartet.

> **Hinweis:** `map: share:rw` in `config.yaml` ist zwingend erforderlich, damit das Add-on in den Host-Share-Ordner schreiben kann.

---

### Integration `tower_hardware`

Die Integration verbindet Home Assistant per SSH mit dem Host und steuert die Binaries.

**Konfiguration (Config Flow, Ersteinrichtung):**
- SSH-Host, Port, Nutzer
- SSH-Key-Pfad und known_hosts
- Pfad zu LED-, OLED- und Lüfter-Binary

**OLED-Seitenrotation (Optionen, nach Ersteinrichtung):**

Über den **Konfigurieren/Optionen**-Button beim Tower-Hardware-Gerät:
- Wechselintervall in Sekunden (5–3600)
- Bis zu 6 Seiten, pro Seite:
  - **Entity**: HA-Entity-ID (per Dropdown auswählbar)
  - **Bezeichnung**: optionaler Titel (Zeile 1, max. 20 Zeichen)
  - **Einheit**: optionales Suffix hinter dem Wert (z. B. `°C`, `W`)

Die Integration liest den State der Entities direkt aus HA, formatiert den Text und sendet ihn per SSH an das OLED. Leere Seiten werden übersprungen.

**Anzeigeformat:**
- Mit Bezeichnung: Zeile 1 = Bezeichnung, Zeile 2 = Wert + Einheit
- Ohne Bezeichnung: eine Zeile mit Wert + Einheit

---

**Entitäten** (alle unter dem Gerät „Tower Hardware" gruppiert):

| Entity | Typ | Beschreibung |
|---|---|---|
| `light.tower_hardware_led` | Light | LED: Farbe (RGB), Helligkeit, Effekte (Blink Slow/Fast, Rainbow, Pulse) |
| `text.tower_hardware_oled_text` | Text | OLED direkt beschreiben (1–3 Zeilen via `\n`, je max. 20 Zeichen) |
| `fan.tower_hardware_fan` | Fan | Lüfter: Drehzahl (0–100 %), Preset Auto/Manuell; `turn_off` = Auto-Modus |
| `sensor.tower_hardware_cpu_temperature` | Sensor | CPU-Temperatur des Hosts in °C |
| `binary_sensor.tower_hardware_led_available` | Binary Sensor | LED-Binary auf dem Host vorhanden |
| `binary_sensor.tower_hardware_oled_available` | Binary Sensor | OLED-Binary auf dem Host vorhanden |
| `binary_sensor.tower_hardware_fan_available` | Binary Sensor | Lüfter-Binary auf dem Host vorhanden |

> **Hinweis:** Die genauen Entity-IDs hängen von der HA-Version und Erstregistrierung ab. Im Zweifelsfall unter **Entwicklerwerkzeuge → Zustände** nachschlagen.

> **Migration von 0.1.x:** Die Entities `text.tower_hardware_oled_page_1/2/3` und `number.tower_hardware_oled_rotation_interval` wurden in 0.2.0 entfernt. Sie erscheinen in der Registry als „unavailable" und können manuell gelöscht werden. Die OLED-Rotation erfolgt jetzt direkt über die Integrationsoptionen.

---

**Interner Ablauf:**
1. Coordinator pollt zyklisch den Zustand (alle 20 s) via SSH.
2. API prüft Verfügbarkeit der Binaries (`test -x ...`).
3. Befehle werden per SSH remote ausgeführt.
4. OLED-Rotation läuft unabhängig davon per `async_track_time_interval`.
5. Bei Optionsänderung wird der Rotations-Timer automatisch neu gestartet.

---

### Packages-Datei `packages/tower_control.yaml`

> **Hinweis für 0.2.0-Nutzer:** Die OLED-Rotationsautomationen in dieser Datei sind seit 0.2.0 deprecated — die Rotation läuft jetzt intern in der Integration. Nur der **LED-Startup-Effekt** ist noch relevant.

**LED-Startup-Effekt:**
- 15 Sekunden nach HA-Start wird die LED automatisch auf den Regenbogen-Effekt gesetzt.

**Aktivierung (nur LED-Startup-Effekt):**
1. `configuration.yaml` um Packages-Unterstützung erweitern:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. `packages/tower_control.yaml` nach `/config/packages/` kopieren.
3. Home Assistant neu starten.

---

## 🇬🇧 English

### Add-on `tower_control`

The add-on builds and deploys the native host tools on startup.

**Key files:**
- `addons/tower_control/config.yaml`: add-on metadata, options, schema
- `addons/tower_control/run.sh`: startup logic, option mapping, binary deployment
- `addons/tower_control/tower_ledctl.c`: LED control incl. effects
- `addons/tower_control/tower_oledctl.c`: OLED text output (1–3 lines)
- `addons/tower_control/tower_fanctl.c`: temperature-controlled fan daemon

**Startup flow:**
1. Add-on reads options via `bashio::config` from `config.yaml`.
2. Binaries are copied to `/share/tower_control/` (= `/mnt/data/supervisor/share/tower_control/` on the host).
3. `tower_fanctl` is launched as a background daemon.

> **Note:** `map: share:rw` in `config.yaml` is mandatory so the add-on container can write to the host share folder.

---

### Integration `tower_hardware`

The integration connects Home Assistant to host binaries via SSH.

**Configuration (Config Flow, initial setup):**
- SSH host, port, user
- SSH key path and known_hosts
- Paths to LED, OLED, and fan binaries

**OLED page rotation (Options, after initial setup):**

Via the **Configure/Options** button on the Tower Hardware device entry:
- Rotation interval in seconds (5–3600)
- Up to 6 pages, per page:
  - **Entity**: HA entity ID (selectable via dropdown)
  - **Label**: optional title (line 1, max. 20 characters)
  - **Unit**: optional suffix after the value (e.g. `°C`, `W`)

The integration reads entity states directly from HA, formats the text, and sends it to the OLED over SSH. Empty page slots are skipped.

**Display format:**
- With label: line 1 = label, line 2 = value + unit
- Without label: single line with value + unit

---

**Entities** (all grouped under the "Tower Hardware" device):

| Entity | Type | Description |
|---|---|---|
| `light.tower_hardware_led` | Light | LED: RGB color, brightness, effects (Blink Slow/Fast, Rainbow, Pulse) |
| `text.tower_hardware_oled_text` | Text | Write directly to OLED (1–3 lines via `\n`, max. 20 chars each) |
| `fan.tower_hardware_fan` | Fan | Fan: speed (0–100 %), preset Auto/Manual; `turn_off` = switches to auto mode |
| `sensor.tower_hardware_cpu_temperature` | Sensor | Host CPU temperature in °C |
| `binary_sensor.tower_hardware_led_available` | Binary Sensor | LED binary present on host |
| `binary_sensor.tower_hardware_oled_available` | Binary Sensor | OLED binary present on host |
| `binary_sensor.tower_hardware_fan_available` | Binary Sensor | Fan binary present on host |

> **Note on entity IDs:** Exact IDs depend on the HA version and first-registration. Check under **Developer Tools → States** if in doubt.

> **Migration from 0.1.x:** The entities `text.tower_hardware_oled_page_1/2/3` and `number.tower_hardware_oled_rotation_interval` were removed in 0.2.0. They will appear as "unavailable" in the entity registry and can be manually deleted. OLED rotation is now configured directly in the integration options.

---

**Internal flow:**
1. Coordinator polls state every 20 s via SSH.
2. API checks binary availability (`test -x ...`).
3. Commands are executed remotely over SSH.
4. OLED rotation runs independently via `async_track_time_interval`.
5. When options change, the rotation timer is automatically restarted.

---

### Packages file `packages/tower_control.yaml`

> **Note for 0.2.0 users:** The OLED rotation automations in this file are deprecated as of 0.2.0 — rotation is now handled internally by the integration. Only the **LED startup effect** remains relevant.

**LED startup effect:**
- 15 seconds after HA starts, the LED is automatically set to the Rainbow effect.

**Setup (LED startup effect only):**
1. Enable packages support in `configuration.yaml`:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. Copy `packages/tower_control.yaml` to `/config/packages/`.
3. Restart Home Assistant.
