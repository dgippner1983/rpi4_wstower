# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_FAN_BINARY, DEFAULT_FAN_BINARY, DOMAIN, PLATFORMS
from .coordinator import TowerCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.version < 2:
        new_data = {**entry.data}
        new_data.setdefault(CONF_FAN_BINARY, DEFAULT_FAN_BINARY)
        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = TowerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.start_oled_rotation()
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    return True


async def _options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator: TowerCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.stop_oled_rotation()
    coordinator.start_oled_rotation()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: TowerCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        coordinator.stop_oled_rotation()
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
