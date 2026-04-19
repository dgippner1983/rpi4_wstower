# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TowerBaseEntity

OLED_MODE_MANUAL = "Manuell"
OLED_MODE_AUTO = "Automatisch"
OLED_MODES = [OLED_MODE_MANUAL, OLED_MODE_AUTO]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([OledModeSelect(hass.data[DOMAIN][entry.entry_id])], True)


class OledModeSelect(TowerBaseEntity, SelectEntity):
    _attr_name = "OLED Modus"
    _attr_has_entity_name = True
    _attr_unique_id = "tower_hardware_oled_mode"
    _attr_options = OLED_MODES

    @property
    def current_option(self) -> str:
        return OLED_MODE_AUTO if self.coordinator.oled_mode == "auto" else OLED_MODE_MANUAL

    async def async_select_option(self, option: str) -> None:
        mode = "auto" if option == OLED_MODE_AUTO else "manual"
        self.coordinator.async_set_oled_mode(mode)
        self.async_write_ha_state()
