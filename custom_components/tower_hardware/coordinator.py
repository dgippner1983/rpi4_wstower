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
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import TowerApi
from .const import CONF_OLED_PAGES, CONF_OLED_ROTATION_INTERVAL, DEFAULT_OLED_ROTATION_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TowerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.api = TowerApi(entry.data)
        self._entry = entry
        self._oled_page_index = 0
        self._oled_unsub = None
        self.oled_mode: str = "auto"
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

    def async_set_oled_mode(self, mode: str) -> None:
        self.oled_mode = mode
        if mode == "auto":
            self.start_oled_rotation()
        else:
            self.stop_oled_rotation()

    def start_oled_rotation(self) -> None:
        self.stop_oled_rotation()
        if self.oled_mode != "auto":
            return
        pages = self._entry.options.get(CONF_OLED_PAGES, [])
        if not pages:
            return
        interval = self._entry.options.get(CONF_OLED_ROTATION_INTERVAL, DEFAULT_OLED_ROTATION_INTERVAL)
        self._oled_unsub = async_track_time_interval(
            self.hass,
            self._rotate_oled,
            timedelta(seconds=interval),
        )

    def stop_oled_rotation(self) -> None:
        if self._oled_unsub:
            self._oled_unsub()
            self._oled_unsub = None

    async def _rotate_oled(self, now) -> None:
        pages = self._entry.options.get(CONF_OLED_PAGES, [])
        if not pages:
            return
        self._oled_page_index = (self._oled_page_index + 1) % len(pages)
        page = pages[self._oled_page_index]

        entity_id = page.get("entity", "")
        if not entity_id:
            return

        state = self.hass.states.get(entity_id)
        if not state or state.state in ("unknown", "unavailable"):
            return
        value = state.state
        unit = page.get("unit", "")
        label = page.get("label", "")

        value_str = f"{value} {unit}".strip() if unit else value
        text = f"{label}\n{value_str}" if label else value_str

        try:
            await self.api.oled_text(text)
        except Exception as err:
            _LOGGER.warning("OLED rotation failed: %s", err)

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
