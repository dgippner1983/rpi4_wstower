# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TowerBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TowerOledText(coordinator)], True)


class TowerOledText(TowerBaseEntity, TextEntity):
    _attr_name = "OLED Text"
    _attr_has_entity_name = True
    _attr_unique_id = "tower_hardware_oled_text"
    _attr_native_max = 120
    _attr_mode = "text"

    @property
    def available(self):
        return self.coordinator.data["oled"]["available"]

    @property
    def native_value(self):
        return self.coordinator.data["oled"]["last_text"] or ""

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_oled_text(value)
