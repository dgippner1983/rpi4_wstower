# Tower Control 0.3.2.1

Enthält die OLED- und LED-Steuerung für den [Waveshare PI4B Mini Tower Acce](https://www.waveshare.com/wiki/PI4B_Mini_Tower_Acce#Connection_Details)

## Dateien
- `tower_ledctl.c` – LED-Steuerung mit Effekten
- `tower_oledctl.c` – OLED-Textausgabe
- `tower_fanctl.c` – Temperaturgesteuerter Lüfter-Daemon
- `gen_overpass_font.py` – Font-Header-Erzeugung
- `Dockerfile` – Multi-Stage-Build für die Host-Binaries
- `run.sh` – Add-on-Startskript
- `config.yaml` – Home-Assistant-Add-on-Konfiguration

## Add-on-Optionen

```yaml
options:
  led_count: 8         # Anzahl LEDs
  led_gpio: 21         # GPIO-Pin (WS2812)
  led_dma: 10          # DMA-Kanal
  brightness_limit: 255
  strip_type: GRB      # Farbreihenfolge: GRB|RGB|BRG|RBG|BGR|GBR
  fan_gpio: 14         # GPIO-Pin (Lüfter)
  fan_off_temp: 40     # Lüfter aus unterhalb °C
  fan_min_temp: 45     # Rampe beginnt ab °C
  fan_max_temp: 75     # Vollgas ab °C
  fan_min_duty: 25     # Minimaler Duty-Cycle %
```

## LED-CLI (`tower_ledctl`)

```sh
tower_ledctl off
tower_ledctl color <R> <G> <B> <BRIGHTNESS>   # Werte 0–255
tower_ledctl effect blink_slow
tower_ledctl effect blink_fast
tower_ledctl effect rainbow
tower_ledctl effect pulse
```

## OLED-CLI (`tower_oledctl`)

```sh
tower_oledctl clear
tower_oledctl text "Zeile 1"
tower_oledctl text2 "Zeile 1" "Zeile 2"
tower_oledctl text3 "Zeile 1" "Zeile 2" "Zeile 3"
```

## Lüfter-CLI (`tower_fanctl`)

```sh
tower_fanctl            # Daemon starten (temperaturgesteuert)
tower_fanctl auto       # Zurück zu automatischer Regelung
tower_fanctl off        # Lüfter aus (0 %)
tower_fanctl on         # Vollgas (100 %)
tower_fanctl <0-100>    # Fester Duty-Cycle in Prozent
```
