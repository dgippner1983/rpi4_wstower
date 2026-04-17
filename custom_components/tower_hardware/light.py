# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import TowerBaseEntity

EFFECTS = ["Blink Slow", "Blink Fast", "Rainbow", "Pulse"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([TowerLedLight(hass.data[DOMAIN][entry.entry_id])], True)


class TowerLedLight(TowerBaseEntity, LightEntity):
    _attr_name = "LED"
    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = EFFECTS
    _attr_unique_id = "tower_hardware_led"

    @property
    def available(self):
        return self.coordinator.data["led"]["available"]

    @property
    def is_on(self):
        return self.coordinator.data["led"]["is_on"]

    @property
    def brightness(self):
        return self.coordinator.data["led"]["brightness"]

    @property
    def rgb_color(self):
        d = self.coordinator.data["led"]
        return (d["r"], d["g"], d["b"])

    @property
    def effect(self):
        return self.coordinator.data["led"]["effect"]

    async def async_turn_on(self, **kwargs):
        if "effect" in kwargs and kwargs["effect"]:
            await self.coordinator.async_led_effect(kwargs["effect"])
            return

        r, g, b = self.rgb_color
        brightness = self.brightness
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS])

        await self.coordinator.async_led_color(int(r), int(g), int(b), int(brightness))

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_led_off()
