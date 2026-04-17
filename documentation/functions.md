# Tower Control – Funktionsdokumentation / Feature Documentation

## 🇩🇪 Deutsch

### Add-on `tower_control`

Das Add-on baut/stellt die nativen Host-Tools bereit und startet sie mit den konfigurierten Optionen.

**Wichtige Dateien:**
- `addons/tower_control/config.yaml`: Add-on-Metadaten, Optionen und Schema
- `addons/tower_control/run.sh`: Startlogik und Übergabe der Optionen
- `addons/tower_control/tower_ledctl.c`: LED-Steuerung inkl. Effekte
- `addons/tower_control/tower_oledctl.c`: OLED-Textausgabe

### Integration `tower_hardware`

Die Integration verbindet Home Assistant per SSH mit dem Host und steuert die Binaries.

**Konfiguration (Config Flow):**
- SSH-Host, Port, Nutzer
- SSH-Key-Pfad und known_hosts
- Pfad zu LED-, OLED- und Lüfter-Binary

**Entitäten** (alle unter dem Gerät „Tower Hardware" gruppiert):

| Entity | Typ | Beschreibung |
|---|---|---|
| `light.tower_hardware_led` | Light | LED: Farbe (RGB), Helligkeit, Effekte |
| `text.tower_hardware_oled_text` | Text | OLED direkt beschreiben (1–3 Zeilen, je max. 20 Z.) |
| `text.tower_hardware_oled_page_1` | Text | Inhalt Seite 1 für Rotation (max. 120 Z., `\n` für Zeilenumbruch) |
| `text.tower_hardware_oled_page_2` | Text | Inhalt Seite 2 für Rotation |
| `text.tower_hardware_oled_page_3` | Text | Inhalt Seite 3 für Rotation |
| `number.tower_hardware_oled_rotation_interval` | Number | Wechselfrequenz in Sekunden (5–3600, Standard 30) |
| `fan.tower_hardware_fan` | Fan | Lüfter: Drehzahl (0–100 %), Preset Auto/Manuell |
| `sensor.tower_hardware_cpu_temperature` | Sensor | CPU-Temperatur des Hosts in °C |
| `binary_sensor.tower_hardware_led_available` | Binary Sensor | LED-Binary vorhanden |
| `binary_sensor.tower_hardware_oled_available` | Binary Sensor | OLED-Binary vorhanden |

> **Hinweis zu Entity-IDs:** Die genauen IDs hängen von der HA-Version und Erstregistrierung ab. Im Zweifelsfall unter **Entwicklerwerkzeuge → Zustände** nachschlagen.

**Ablauf:**
1. Coordinator pollt zyklisch den Zustand (alle 20 s).
2. API prüft Verfügbarkeit der Binaries (`test -x ...`).
3. Befehle werden per SSH remote ausgeführt.
4. State-Änderungen werden in Home Assistant aktualisiert.

### OLED-Seitenrotation und Presets (`packages/tower_control.yaml`)

Das Paket `packages/tower_control.yaml` stellt OLED-Rotation, Presets und LED-Startup-Effekt bereit.

**Aktivierung:**
1. `configuration.yaml` um Packages-Unterstützung erweitern:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. `packages/tower_control.yaml` aus dem Repository nach `/config/packages/` kopieren.
3. Home Assistant neu starten.

**Rotation:**
- Ein `input_number` (1–3) verfolgt die aktuelle Seite.
- Ein `timer` steuert den Wechsel-Takt (Dauer aus `number.tower_hardware_oled_rotation_interval`).
- Bei Timer-Ablauf wird der Seitenzähler per Modulo weitergeschaltet (`(n % 3) + 1`), der Text aus dem entsprechenden `text.tower_hardware_oled_page_*`-Slot gelesen und per `text.set_value` an `text.tower_hardware_oled_text` übergeben.
- Leere Slots werden übersprungen (OLED bleibt unverändert).
- Der Timer startet neu bei HA-Start und bei Änderung der Wechselfrequenz.

**Voreinstellungen (`input_select.tower_oled_preset`):**

| Option | Seite 1 | Seite 2 | Seite 3 |
|---|---|---|---|
| Eigener Inhalt | frei (manuell befüllen) | frei | frei |
| System-Info | `HA Online` | Datum + Uhrzeit (2 Zeilen) | CPU-Temperatur |
| Entitäten | Datum + Uhrzeit (2 Zeilen) | Entity 1: Name (10 Z.) + Wert | Entity 2: Name (10 Z.) + Wert |

Bei aktiver Voreinstellung (nicht „Eigener Inhalt") werden die Seiteninhalte jede Minute automatisch aktualisiert. Die Entity-IDs für Preset „Entitäten" werden in `input_text.tower_oled_entity_1` und `input_text.tower_oled_entity_2` eingetragen.

**LED-Startup-Effekt:**
- 15 Sekunden nach HA-Start wird die LED automatisch auf den Regenbogen-Effekt gesetzt.

## 🇬🇧 English

### Add-on `tower_control`

The add-on builds/deploys native host tools and starts them with configured options.

**Key files:**
- `addons/tower_control/config.yaml`: add-on metadata, options, schema
- `addons/tower_control/run.sh`: startup logic and option mapping
- `addons/tower_control/tower_ledctl.c`: LED control incl. effects
- `addons/tower_control/tower_oledctl.c`: OLED text output

### Integration `tower_hardware`

The integration connects Home Assistant to host binaries via SSH.

**Configuration (Config Flow):**
- SSH host, port, user
- SSH key path and known_hosts
- Paths to LED, OLED, and fan binaries

**Entities** (all grouped under the "Tower Hardware" device):

| Entity | Type | Description |
|---|---|---|
| `light.tower_hardware_led` | Light | LED: RGB color, brightness, effects |
| `text.tower_hardware_oled_text` | Text | Write directly to OLED (1–3 lines, max. 20 chars each) |
| `text.tower_hardware_oled_page_1` | Text | Page 1 content for rotation (max. 120 chars, `\n` for line break) |
| `text.tower_hardware_oled_page_2` | Text | Page 2 content for rotation |
| `text.tower_hardware_oled_page_3` | Text | Page 3 content for rotation |
| `number.tower_hardware_oled_rotation_interval` | Number | Page switch interval in seconds (5–3600, default 30) |
| `fan.tower_hardware_fan` | Fan | Fan: speed (0–100 %), preset Auto/Manual |
| `sensor.tower_hardware_cpu_temperature` | Sensor | Host CPU temperature in °C |
| `binary_sensor.tower_hardware_led_available` | Binary Sensor | LED binary present on host |
| `binary_sensor.tower_hardware_oled_available` | Binary Sensor | OLED binary present on host |

> **Note on entity IDs:** Exact IDs depend on the HA version and first-registration. Check under **Developer Tools → States** if in doubt.

**Flow:**
1. Coordinator polls state every 20 s.
2. API checks binary availability (`test -x ...`).
3. Commands are executed remotely over SSH.
4. Entity states are refreshed in Home Assistant.

### OLED Page Rotation and Presets (`packages/tower_control.yaml`)

The `packages/tower_control.yaml` file provides OLED rotation, presets, and an LED startup effect.

**Setup:**
1. Enable packages support in `configuration.yaml`:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. Copy `packages/tower_control.yaml` from this repository to `/config/packages/`.
3. Restart Home Assistant.

**Rotation:**
- An `input_number` (1–3) tracks the current page.
- A `timer` controls the switch cadence (duration from `number.tower_hardware_oled_rotation_interval`).
- On timer expiry, the page counter advances via modulo (`(n % 3) + 1`), the text from the matching `text.tower_hardware_oled_page_*` slot is read and pushed to `text.tower_hardware_oled_text` via `text.set_value`.
- Empty slots are skipped (OLED remains unchanged).
- The timer restarts on HA start and whenever the interval entity changes.

**Presets (`input_select.tower_oled_preset`):**

| Option | Page 1 | Page 2 | Page 3 |
|---|---|---|---|
| Custom | free (edit manually) | free | free |
| System-Info | `HA Online` | Date + time (2 lines) | CPU temperature |
| Entities | Date + time (2 lines) | Entity 1: name (10 chars) + value | Entity 2: name (10 chars) + value |

When a preset is active (not "Custom"), page contents are refreshed every minute. Entity IDs for the "Entities" preset are configured via `input_text.tower_oled_entity_1` and `input_text.tower_oled_entity_2`.

**LED startup effect:**
- 15 seconds after HA start, the LED is automatically set to the Rainbow effect.
