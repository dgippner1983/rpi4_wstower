# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import TowerApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TowerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.api = TowerApi(entry.data)
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Tower Hardware",
            manufacturer="Waveshare",
            model="PI4B Mini Tower",
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=20),
        )

    async def _async_update_data(self):
        try:
            return await self.api.probe()
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    async def async_led_off(self):
        await self.api.led_off()
        await self.async_request_refresh()

    async def async_led_color(self, r: int, g: int, b: int, brightness: int):
        await self.api.led_color(r, g, b, brightness)
        await self.async_request_refresh()

    async def async_led_effect(self, name: str):
        await self.api.led_effect(name)
        await self.async_request_refresh()

    async def async_oled_text(self, text: str):
        await self.api.oled_text(text)
        await self.async_request_refresh()

    async def async_fan_set(self, percentage: int):
        await self.api.fan_set(percentage)
        await self.async_request_refresh()

    async def async_fan_auto(self):
        await self.api.fan_auto()
        await self.async_request_refresh()

    async def async_fan_off(self):
        await self.api.fan_off()
        await self.async_request_refresh()


class TowerBaseEntity(CoordinatorEntity):
    """Basisklasse für alle Tower-Hardware-Entities mit gemeinsamer device_info."""

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info
