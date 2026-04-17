# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TowerOledInterval(coordinator)], True)


class TowerOledInterval(RestoreEntity, NumberEntity):
    """Wechselfrequenz für die OLED-Seitenrotation (in Sekunden)."""

    _attr_has_entity_name = True
    _attr_unique_id = "tower_oled_rotation_interval"
    _attr_name = "OLED Rotation Interval"
    _attr_native_min_value = 5.0
    _attr_native_max_value = 3600.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator) -> None:
        super().__init__()
        self._value = 30.0
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = value
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        if (
            (last := await self.async_get_last_state()) is not None
            and last.state not in ("unknown", "unavailable")
        ):
            try:
                self._value = float(last.state)
            except ValueError:
                pass
