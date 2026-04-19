#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

set -euo pipefail

export TOWER_LED_COUNT="$(bashio::config 'led_count')"
export TOWER_LED_GPIO="$(bashio::config 'led_gpio')"
export TOWER_LED_DMA="$(bashio::config 'led_dma')"
export TOWER_LED_BRIGHTNESS="$(bashio::config 'brightness_limit')"
export TOWER_LED_STRIP_TYPE="$(bashio::config 'strip_type')"

export TOWER_FAN_GPIO="$(bashio::config 'fan_gpio')"
export TOWER_FAN_OFF_TEMP="$(bashio::config 'fan_off_temp')"
export TOWER_FAN_MIN_TEMP="$(bashio::config 'fan_min_temp')"
export TOWER_FAN_MAX_TEMP="$(bashio::config 'fan_max_temp')"
export TOWER_FAN_MIN_DUTY="$(bashio::config 'fan_min_duty')"

bashio::log.info "Tower Control started"
bashio::log.info "LED: count=${TOWER_LED_COUNT}, gpio=${TOWER_LED_GPIO}, dma=${TOWER_LED_DMA}, brightness=${TOWER_LED_BRIGHTNESS}, strip_type=${TOWER_LED_STRIP_TYPE}"
bashio::log.info "Fan: gpio=${TOWER_FAN_GPIO}, off=${TOWER_FAN_OFF_TEMP}C, min=${TOWER_FAN_MIN_TEMP}C, max=${TOWER_FAN_MAX_TEMP}C, min_duty=${TOWER_FAN_MIN_DUTY}%"

TARGET="/share/tower_control"
mkdir -p "$TARGET"

cp /usr/local/bin/tower_oledctl "$TARGET/tower_oledctl"
cp /usr/local/bin/tower_ledctl  "$TARGET/tower_ledctl"
cp /usr/local/bin/tower_fanctl  "$TARGET/tower_fanctl"

chmod +x "$TARGET/tower_oledctl" "$TARGET/tower_ledctl" "$TARGET/tower_fanctl"

bashio::log.info "Tower Control tools deployed:"
ls -l "$TARGET"

bashio::log.info "Playing startup animation"
"$TARGET/tower_oledctl" startup || true

"$TARGET/tower_fanctl" &
bashio::log.info "Fan controller started (PID $!)"

wait
