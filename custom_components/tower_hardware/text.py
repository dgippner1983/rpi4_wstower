# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import TowerBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TowerOledText(coordinator),
            TowerOledPage(coordinator, 1),
            TowerOledPage(coordinator, 2),
            TowerOledPage(coordinator, 3),
        ],
        True,
    )


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


class TowerOledPage(RestoreEntity, TextEntity):
    """Speicherslot für eine OLED-Anzeigeseite (kein direkter Hardware-Zugriff)."""

    _attr_has_entity_name = True
    _attr_native_max = 120
    _attr_mode = "text"

    def __init__(self, coordinator, slot: int) -> None:
        super().__init__()
        self._value = ""
        self._attr_name = f"OLED Page {slot}"
        self._attr_unique_id = f"tower_oled_page_{slot}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> str:
        return self._value

    async def async_set_value(self, value: str) -> None:
        self._value = value
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        if (
            (last := await self.async_get_last_state()) is not None
            and last.state not in ("unknown", "unavailable")
        ):
            self._value = last.state
