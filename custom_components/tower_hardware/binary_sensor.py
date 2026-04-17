# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TowerBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LedAvailable(c), OledAvailable(c), FanAvailable(c)], True)


class _B(TowerBaseEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)


class LedAvailable(_B):
    _attr_name = "LED Available"
    _attr_has_entity_name = True
    _attr_unique_id = "tower_led_available"

    @property
    def is_on(self):
        return self.coordinator.data["led"]["available"]


class OledAvailable(_B):
    _attr_name = "OLED Available"
    _attr_has_entity_name = True
    _attr_unique_id = "tower_oled_available"

    @property
    def is_on(self):
        return self.coordinator.data["oled"]["available"]


class FanAvailable(_B):
    _attr_name = "Fan Available"
    _attr_has_entity_name = True
    _attr_unique_id = "tower_fan_available"

    @property
    def is_on(self):
        return self.coordinator.data["fan"]["available"]
