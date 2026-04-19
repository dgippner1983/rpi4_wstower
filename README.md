# Tower Control for Home Assistant 0.3.0

## 🇬🇧 English

This repository provides a complete package for using the Raspberry Pi 4 [Waveshare PI4B Mini Tower Acce](https://www.waveshare.com/wiki/PI4B_Mini_Tower_Acce#Connection_Details) with Home Assistant:

- **Home Assistant Add-on** to deploy native host control binaries (`tower_ledctl`, `tower_oledctl`, `tower_fanctl`)
- **Custom Integration** (`tower_hardware`) for LED, OLED, and fan control directly in Home Assistant
- **HACS-compatible layout** so the integration can be installed from a custom repository

### Included components

- Add-on: `addons/tower_control`
- Integration (HACS/custom component): `custom_components/tower_hardware`

### Features

- LED exposed as a `light` entity with color, brightness, and effects: Blink Slow/Fast, Rainbow, Pulse, **Fire**, **Color Wipe**
- OLED direct control via a `text` entity with up to 3 lines
- **OLED page rotation built-in**: configure up to 6 HA entities in the integration options — rotates automatically, no automations required
- **OLED mode select**: switch between *Manual* (static text) and *Automatic* (page rotation) at runtime via a `select` entity
- Fan exposed as a `fan` entity with speed control (0–100 %) and Auto/Manual preset; `turn_off` switches to automatic temperature control
- **Startup animation**: on add-on start, a pixel-art raspberry travels across the OLED display toward a house
- CPU temperature, **RAM free %**, and **Disk free %** as `sensor` entities
- LED/OLED/fan availability as `binary_sensor` entities
- All entities grouped under a single **Tower Hardware** device
- Configurable SSH execution for host-side binaries
- Optional: `packages/tower_control.yaml` for an LED startup rainbow effect

### Prerequisites

**Disable onboard audio (required for LED control)**

The LED strip is driven via GPIO 18, which uses the Raspberry Pi's PWM0 peripheral. On recent kernels the onboard audio driver claims PWM0, causing `ws2811_init` to hang and LED commands to time out. Disabling the onboard audio driver frees PWM0 for LED use.

Add the following line to `/mnt/boot/config.txt` on the HA OS host and reboot:

```
dtparam=audio=off
```

> **Note:** This only disables the 3.5 mm onboard audio output. USB sound cards are completely unaffected.

### Add-on installation (Home Assistant Add-on Repository)

1. Host this repository on Codeberg (or GitHub).
2. In Home Assistant: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
3. Add your repository URL.
4. Install and start the **Tower Control** add-on.

### Integration installation via HACS

1. In HACS: **Integrations → ⋮ → Custom repositories**.
2. Add the repository URL and choose category **Integration**.
3. Install **Tower Hardware**.
4. Restart Home Assistant.
5. Add the integration via **Settings → Devices & Services**.

Default integration binary paths:

- LED: `/mnt/data/supervisor/share/tower_control/tower_ledctl`
- OLED: `/mnt/data/supervisor/share/tower_control/tower_oledctl`
- Fan: `/mnt/data/supervisor/share/tower_control/tower_fanctl`

### OLED page rotation setup

After adding the integration, click **Configure** (or **Options**) on the Tower Hardware entry:

- Set the **rotation interval** (seconds).
- For each page (up to 6): select an entity from the dropdown, optionally enter a label and unit.

The integration will then automatically display and rotate the pages. Empty page slots are skipped.

**Display format per page:**
- With label: line 1 = label, line 2 = value + unit
- Without label: single line with value + unit

### SSH key setup

The integration connects to the HA host via SSH to execute the control binaries. Key-based authentication is required.

> **No SSH host access yet?** SSH access to the underlying HAOS host (port 22222) is not enabled by default. You can set it up using the community add-on [HassOS SSH Port 22222 Configurator](https://community.home-assistant.io/t/add-on-hassos-ssh-port-22222-configurator/264109).

**1. Generate a key pair** (run in the HA terminal or SSH add-on):

```bash
mkdir -p /config/.ssh
ssh-keygen -t ed25519 -f /config/.ssh/id_ed25519 -N ""
```

**2. Authorize the key on the host:**

```bash
ssh-copy-id -i /config/.ssh/id_ed25519.pub -p 22222 root@127.0.0.1
```

Or manually append the contents of `/config/.ssh/id_ed25519.pub` to `/root/.ssh/authorized_keys` on the host.

**3. Test the connection:**

```bash
ssh -i /config/.ssh/id_ed25519 -p 22222 root@127.0.0.1 "echo ok"
```

The integration uses the private key at `/config/.ssh/id_ed25519` by default. This path can be changed during integration setup.

## Documentation

A full feature reference is available in [`documentation/functions.md`](documentation/functions.md).

The [CHANGELOG](CHANGELOG.md) documents all changes per version.

## License

This project is licensed under the **GNU General Public License v3.0 or later** — see [LICENSE](LICENSE) for the full text.

Parts of this software were developed with the assistance of [Claude](https://claude.ai), an AI assistant by Anthropic.

---

## 🇩🇪 Deutsch

Dieses Repository enthält ein vollständiges Paket für den Raspberry Pi 4 [Waveshare PI4B Mini Tower Acce](https://www.waveshare.com/wiki/PI4B_Mini_Tower_Acce#Connection_Details) in Home Assistant:

- **Home Assistant Add-on** zum Bereitstellen der nativen Steuerungs-Binaries auf dem Host (`tower_ledctl`, `tower_oledctl`, `tower_fanctl`)
- **Custom Integration** (`tower_hardware`) zur direkten Einbindung von LED-, OLED- und Lüftersteuerung in Home Assistant
- **HACS-kompatible Struktur**, damit die Integration als Custom Repository installiert werden kann

### Enthaltene Bestandteile

- Add-on: `addons/tower_control`
- Integration (HACS/Custom Component): `custom_components/tower_hardware`

### Funktionsumfang

- LED als `light`-Entity mit Farbe, Helligkeit und Effekten: Blink Slow/Fast, Rainbow, Pulse, **Fire**, **Color Wipe**
- OLED-Direktsteuerung über eine `text`-Entity mit bis zu 3 Zeilen
- **Integrierte OLED-Seitenrotation**: bis zu 6 HA-Entities direkt in den Integrationsoptionen konfigurierbar — rotiert automatisch, keine Automationen nötig
- **OLED-Modus-Auswahl**: zur Laufzeit zwischen *Manuell* (statischer Text) und *Automatisch* (Seitenrotation) wechseln — als `select`-Entity
- Lüfter als `fan`-Entity mit Drehzahlregelung (0–100 %) und Auto/Manuell-Preset; `turn_off` wechselt in den temperaturgesteuerten Automatikmodus
- **Startup-Animation**: beim Add-on-Start wandert eine Pixel-Art-Himbeere über das OLED-Display zu einem Haus
- CPU-Temperatur, **RAM frei %** und **Disk frei %** als `sensor`-Entities
- Verfügbarkeits-Sensoren für LED/OLED/Lüfter als `binary_sensor`
- Alle Entities unter einem gemeinsamen **Tower Hardware**-Gerät gruppiert
- Konfigurierbare SSH-Verbindung zur Ausführung der Host-Binaries
- Optional: `packages/tower_control.yaml` für LED-Startup-Regenbogeneffekt

### Voraussetzungen

**Onboard-Audio deaktivieren (erforderlich für LED-Steuerung)**

Der LED-Streifen wird über GPIO 18 angesteuert, der den PWM0-Baustein des Raspberry Pi nutzt. Auf neueren Kerneln beansprucht der onboard-Audio-Treiber PWM0, wodurch `ws2811_init` hängt und LED-Befehle mit einem SSH-Timeout scheitern. Durch Deaktivieren des Audio-Treibers wird PWM0 für die LED-Steuerung freigegeben.

Folgende Zeile in `/mnt/boot/config.txt` auf dem HA-OS-Host eintragen und anschließend neu starten:

```
dtparam=audio=off
```

> **Hinweis:** Dies deaktiviert nur den onboard-Audio-Ausgang (3,5-mm-Klinke). USB-Soundkarten sind davon nicht betroffen.

### Installation Add-on (Home Assistant Add-on Repository)

1. Dieses Repository in Codeberg (oder GitHub) bereitstellen.
2. In Home Assistant: **Einstellungen → Add-ons → Add-on-Store → ⋮ → Repositories**.
3. Repository-URL eintragen.
4. Add-on **Tower Control** installieren und starten.

### Installation Integration über HACS

1. In HACS: **Integrationen → ⋮ → Benutzerdefinierte Repositories**.
2. Repository-URL eintragen und Kategorie **Integration** auswählen.
3. **Tower Hardware** installieren.
4. Home Assistant neu starten.
5. Integration über **Einstellungen → Geräte & Dienste** hinzufügen.

Standardpfade in der Integration:

- LED: `/mnt/data/supervisor/share/tower_control/tower_ledctl`
- OLED: `/mnt/data/supervisor/share/tower_control/tower_oledctl`
- Lüfter: `/mnt/data/supervisor/share/tower_control/tower_fanctl`

### OLED-Seitenrotation einrichten

Nach dem Hinzufügen der Integration auf **Konfigurieren** (bzw. **Optionen**) beim Tower-Hardware-Eintrag klicken:

- **Wechselintervall** in Sekunden einstellen.
- Pro Seite (bis zu 6): Entity per Dropdown auswählen, optional Bezeichnung und Einheit eintragen.

Die Integration zeigt und rotiert die Seiten dann automatisch. Leere Slots werden übersprungen.

**Anzeigeformat pro Seite:**
- Mit Bezeichnung: Zeile 1 = Bezeichnung, Zeile 2 = Wert + Einheit
- Ohne Bezeichnung: eine Zeile mit Wert + Einheit

### SSH-Schlüssel einrichten

Die Integration verbindet sich per SSH mit dem HA-Host, um die Steuerungs-Binaries auszuführen. Es wird eine schlüsselbasierte Authentifizierung benötigt.

> **Noch kein SSH-Host-Zugriff?** Der SSH-Zugriff auf den HAOS-Host (Port 22222) ist standardmäßig nicht aktiviert. Er kann mit dem Community-Add-on [HassOS SSH Port 22222 Configurator](https://community.home-assistant.io/t/add-on-hassos-ssh-port-22222-configurator/264109) eingerichtet werden.

**1. Schlüsselpaar generieren** (im HA-Terminal oder SSH-Add-on ausführen):

```bash
mkdir -p /config/.ssh
ssh-keygen -t ed25519 -f /config/.ssh/id_ed25519 -N ""
```

**2. Öffentlichen Schlüssel auf dem Host autorisieren:**

```bash
ssh-copy-id -i /config/.ssh/id_ed25519.pub -p 22222 root@127.0.0.1
```

Alternativ den Inhalt von `/config/.ssh/id_ed25519.pub` manuell an `/root/.ssh/authorized_keys` auf dem Host anhängen.

**3. Verbindung testen:**

```bash
ssh -i /config/.ssh/id_ed25519 -p 22222 root@127.0.0.1 "echo ok"
```

Die Integration verwendet standardmäßig den privaten Schlüssel unter `/config/.ssh/id_ed25519`. Der Pfad kann bei der Einrichtung der Integration angepasst werden.

## Dokumentation

Eine vollständige Funktionsreferenz befindet sich in [`documentation/functions.md`](documentation/functions.md).

Der [CHANGELOG](CHANGELOG.md) dokumentiert alle Änderungen je Version.

## Lizenz

Dieses Projekt steht unter der **GNU General Public License v3.0 or later** — der vollständige Text ist in [LICENSE](LICENSE) enthalten.

Teile dieser Software wurden mit Unterstützung von [Claude](https://claude.ai), einem KI-Assistenten von Anthropic, entwickelt.
