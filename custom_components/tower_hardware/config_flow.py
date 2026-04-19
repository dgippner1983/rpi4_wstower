# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_FAN_BINARY,
    CONF_LED_BINARY,
    CONF_OLED_PAGES,
    CONF_OLED_ROTATION_INTERVAL,
    CONF_OLED_BINARY,
    CONF_SSH_HOST,
    CONF_SSH_KEY_PATH,
    CONF_SSH_KNOWN_HOSTS,
    CONF_SSH_PORT,
    CONF_SSH_USER,
    DEFAULT_FAN_BINARY,
    DEFAULT_LED_BINARY,
    DEFAULT_OLED_BINARY,
    DEFAULT_OLED_ROTATION_INTERVAL,
    DEFAULT_SSH_HOST,
    DEFAULT_SSH_KEY_PATH,
    DEFAULT_SSH_KNOWN_HOSTS,
    DEFAULT_SSH_PORT,
    DEFAULT_SSH_USER,
    DOMAIN,
    MAX_OLED_PAGES,
)


class TowerHardwareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Tower Hardware", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_SSH_HOST, default=DEFAULT_SSH_HOST): str,
            vol.Required(CONF_SSH_PORT, default=DEFAULT_SSH_PORT): int,
            vol.Required(CONF_SSH_USER, default=DEFAULT_SSH_USER): str,
            vol.Required(CONF_SSH_KEY_PATH, default=DEFAULT_SSH_KEY_PATH): str,
            vol.Required(CONF_SSH_KNOWN_HOSTS, default=DEFAULT_SSH_KNOWN_HOSTS): str,
            vol.Required(CONF_LED_BINARY, default=DEFAULT_LED_BINARY): str,
            vol.Required(CONF_OLED_BINARY, default=DEFAULT_OLED_BINARY): str,
            vol.Required(CONF_FAN_BINARY, default=DEFAULT_FAN_BINARY): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(config_entry):
        return TowerHardwareOptionsFlow(config_entry)


class TowerHardwareOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            pages = []
            for i in range(1, MAX_OLED_PAGES + 1):
                entity = (user_input.get(f"page_{i}_entity") or "").strip()
                if entity:
                    pages.append({
                        "entity": entity,
                        "label": (user_input.get(f"page_{i}_label") or "").strip(),
                        "unit": (user_input.get(f"page_{i}_unit") or "").strip(),
                    })
            return self.async_create_entry(title="", data={
                CONF_OLED_PAGES: pages,
                CONF_OLED_ROTATION_INTERVAL: int(float(
                    user_input.get(CONF_OLED_ROTATION_INTERVAL, DEFAULT_OLED_ROTATION_INTERVAL)
                )),
            })

        existing_pages = self._entry.options.get(CONF_OLED_PAGES, [])
        interval = self._entry.options.get(CONF_OLED_ROTATION_INTERVAL, DEFAULT_OLED_ROTATION_INTERVAL)

        schema_dict = {
            vol.Optional(CONF_OLED_ROTATION_INTERVAL): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=3600, step=1, unit_of_measurement="s", mode="box")
            ),
        }
        for i in range(1, MAX_OLED_PAGES + 1):
            page = existing_pages[i - 1] if i - 1 < len(existing_pages) else {}
            schema_dict[vol.Optional(f"page_{i}_entity")] = selector.EntitySelector()
            schema_dict[vol.Optional(f"page_{i}_label")] = selector.TextSelector()
            schema_dict[vol.Optional(f"page_{i}_unit")] = selector.TextSelector()

        suggested = {CONF_OLED_ROTATION_INTERVAL: interval}
        for i in range(1, MAX_OLED_PAGES + 1):
            page = existing_pages[i - 1] if i - 1 < len(existing_pages) else {}
            if page.get("entity"):
                suggested[f"page_{i}_entity"] = page["entity"]
            suggested[f"page_{i}_label"] = page.get("label", "")
            suggested[f"page_{i}_unit"] = page.get("unit", "")

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema_dict), suggested),
        )
