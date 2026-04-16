# Tower Control 0.0.2

Enthält die OLED- und LED-Steuerung für den [Waveshare PI4B Mini Tower Acce](https://www.waveshare.com/wiki/PI4B_Mini_Tower_Acce#Connection_Details)

## Dateien
- `tower_oledctl.c` – OLED-Ausgabe
- `tower_ledctl.c` – LED-Steuerung mit Effekten
- `gen_overpass_font.py` – Font-Header-Erzeugung
- `Dockerfile` – Build für das Add-on-Binary-Image
- `run.sh` – Add-on-Startskript mit Übernahme der Add-on-Optionen
- `config.yaml` – Home-Assistant-Add-on-Konfiguration
- `translations/de.yaml`, `translations/en.yaml` – Bezeichnungen für die Add-on-Optionen

## Add-on-Optionen
Die Farbreihenfolge wird im Add-on konfiguriert, nicht in der Integration.

```yaml
options:
  led_count: 8
  led_gpio: 21
  led_dma: 10
  brightness_limit: 255
  strip_type: GRB
```

Erlaubte Werte für `strip_type`:
- `GRB`
- `RGB`
- `BRG`
- `RBG`
- `BGR`
- `GBR`

Intern setzt `run.sh` diese Option auf die Umgebungsvariable `TOWER_LED_STRIP_TYPE`, die dann von `tower_ledctl` ausgewertet wird.

## LED-CLI

Beispiele:

```sh
/usr/local/bin/tower_ledctl off
/usr/local/bin/tower_ledctl solid FF8800
/usr/local/bin/tower_ledctl solid 00FF00 96
/usr/local/bin/tower_ledctl blink FF0000 300 10
/usr/local/bin/tower_ledctl breathe 00AAFF 2000
/usr/local/bin/tower_ledctl pulse 00FF00 1200 160
/usr/local/bin/tower_ledctl chase FFFFFF 101010 100
/usr/local/bin/tower_ledctl rainbow 40 128
```

## Umgebungsvariablen
Optional überschreibbar:

```sh
TOWER_LED_COUNT=8
TOWER_LED_GPIO=21
TOWER_LED_DMA=10
TOWER_LED_BRIGHTNESS=255
TOWER_LED_STRIP_TYPE=GRB
```

## Unterstützte Effekte
- `off`
- `solid`
- `blink`
- `breathe`
- `pulse`
- `chase`
- `rainbow`
