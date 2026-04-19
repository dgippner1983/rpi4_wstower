# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import TowerBaseEntity

PRESET_AUTO = "Auto"
PRESET_MANUAL = "Manuell"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([TowerFan(hass.data[DOMAIN][entry.entry_id])], True)


class TowerFan(TowerBaseEntity, FanEntity):
    _attr_name = "Fan"
    _attr_has_entity_name = True
    _attr_unique_id = "tower_hardware_fan"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [PRESET_AUTO, PRESET_MANUAL]
    _attr_speed_count = 100

    @property
    def available(self) -> bool:
        return self.coordinator.data["fan"]["available"]

    @property
    def is_on(self) -> bool:
        return self.coordinator.data["fan"]["duty"] > 0

    @property
    def percentage(self) -> int:
        return self.coordinator.data["fan"]["duty"]

    @property
    def preset_mode(self) -> str:
        return PRESET_AUTO if self.coordinator.data["fan"]["mode"] == "auto" else PRESET_MANUAL

    async def async_turn_on(self, percentage: int | None = None,
                            preset_mode: str | None = None, **kwargs) -> None:
        if preset_mode == PRESET_AUTO:
            await self.coordinator.async_fan_auto()
            return
        pct = percentage if percentage is not None else (self.percentage or 50)
        await self.coordinator.async_fan_set(int(pct))

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_fan_auto()

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.coordinator.async_fan_auto()
        else:
            await self.coordinator.async_fan_set(percentage)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_AUTO:
            await self.coordinator.async_fan_auto()
        else:
            pct = self.percentage or 50
            await self.coordinator.async_fan_set(pct)
