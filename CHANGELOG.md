# Changelog

Alle wesentlichen Änderungen an diesem Projekt sind hier dokumentiert.
All notable changes to this project are documented here.

Das Format folgt [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] – 2026-04-19

### Integration `tower_hardware`

#### Neu / Added
- **OLED-Seitenrotation intern** — bis zu 6 HA-Entities direkt in den
  Integrationsoptionen konfigurierbar (Entity-ID, Bezeichnung, Einheit).
  Der Coordinator rotiert die Seiten automatisch per `async_track_time_interval`;
  Automationen für die Rotation werden nicht mehr benötigt.
- **OptionsFlow** — nach der Ersteinrichtung über den „Optionen"-Button
  in HA konfigurierbar: Entity-Auswahl per Dropdown, Wechselintervall (5–3600 s).
- **`fan.turn_off` → Auto-Modus** — Ausschalten des Lüfters über die HA-UI
  oder Automatisierungen übergibt die Steuerung zurück an die
  temperaturbasierte Automatik des Daemons (statt hart auszuschalten).
  Gleiches gilt für das Setzen der Drehzahl auf 0 %.

#### Entfernt / Removed
- `text.tower_hardware_oled_page_1/2/3` — ersetzt durch integrierten OptionsFlow.
  Bestehende Entities in der HA-Registry werden als „unavailable" angezeigt
  und können manuell entfernt werden.
- `number.tower_hardware_oled_rotation_interval` — Wechselintervall wird nun
  in den Optionen der Integration konfiguriert.

#### Geändert / Changed
- `packages/tower_control.yaml`: OLED-Rotationsautomationen sind mit 0.2.0
  deprecated; nur der LED-Startup-Effekt ist noch relevant.

---

### Add-on `tower_control`

#### Geändert / Changed
- **0.1.3**: `map: share:rw` in `config.yaml` ergänzt — ohne diesen Eintrag
  wurden die compilierten Binaries nicht in den Host-Share-Ordner geschrieben
  (`/mnt/data/supervisor/share/tower_control/`). Bugfix für fehlende
  `tower_fanctl` nach Rebuild.

---

## [0.1.1] – 2026-04-17

### Integration `tower_hardware`

#### Neu / Added
- `binary_sensor.tower_hardware_fan_available` — zeigt an ob `tower_fanctl`
  auf dem Host vorhanden ist.
- OLED-Presets: drei vordefinierte Anzeigemuster (Eigener Inhalt, System-Info,
  Entitäten) über `packages/tower_control.yaml`.
- LED-Startup-Effekt: Regenbogen-Effekt 15 s nach HA-Start (via Package).

#### Geändert / Changed
- Entity-Benennung vereinheitlicht.

### Add-on `tower_control`

#### Neu / Added
- `tower_fanctl.c` — temperaturgesteuerter Lüfter-Daemon mit Software-PWM
  über GPIO; unterstützt Auto-, Manual- und Off-Modus.
- `fan_gpio`, `fan_off_temp`, `fan_min_temp`, `fan_max_temp`, `fan_min_duty`
  als konfigurierbare Add-on-Optionen.
- `/dev/gpiomem` in `devices:` ergänzt (für Lüfter-GPIO).

---

## [0.1.0] – 2026-04-17

### Integration `tower_hardware`

#### Neu / Added
- `fan.tower_hardware_fan` — Lüfter-Entity mit Drehzahl (0–100 %) und
  Preset Auto/Manuell.
- `sensor.tower_hardware_cpu_temperature` — CPU-Temperatur des Hosts.
- SSH ControlMaster (`ControlPersist=60`) — reduziert SSH-Verbindungsaufbau
  bei häufigen Befehlen erheblich.

#### Geändert / Changed
- OLED-Rotation und Seiten-Slots (`text.tower_hardware_oled_page_1/2/3`)
  eingeführt; Wechselintervall als `number`-Entity.

---

## [0.0.3] – 2026-04-17

### Integration `tower_hardware`

#### Behoben / Fixed
- Zu viele parallele SSH-Sitzungen durch fehlende ControlMaster-Konfiguration;
  behoben durch SSH-Multiplexing.

---

## [0.0.2] – 2026-04-16

### Integration `tower_hardware`

#### Neu / Added
- Erste öffentliche Version mit LED (`light`), OLED (`text`) und
  SSH-basierter Kommunikation mit dem HA-Host.
- Config Flow für SSH-Credentials und Binary-Pfade.
- `binary_sensor` für LED- und OLED-Verfügbarkeit.

### Add-on `tower_control`

#### Neu / Added
- Multi-Stage Dockerfile: compiliert `tower_ledctl` und `tower_oledctl`
  statisch für `aarch64`, `armv7`, `armhf`.
- `run.sh` deployt Binaries nach `/share/tower_control/`.

---

## [0.0.1] – 2026-04-15

- Initiales Commit: Projektstruktur, Dockerfile-Grundgerüst, erste
  `tower_ledctl.c`- und `tower_oledctl.c`-Implementierungen.
