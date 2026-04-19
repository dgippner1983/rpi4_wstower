# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    CONF_FAN_BINARY,
    CONF_LED_BINARY,
    CONF_OLED_BINARY,
    CONF_SSH_HOST,
    CONF_SSH_KEY_PATH,
    CONF_SSH_KNOWN_HOSTS,
    CONF_SSH_PORT,
    CONF_SSH_USER,
    DEFAULT_FAN_BINARY,
    DEFAULT_LED_BINARY,
    DEFAULT_OLED_BINARY,
    DEFAULT_SSH_HOST,
    DEFAULT_SSH_KEY_PATH,
    DEFAULT_SSH_KNOWN_HOSTS,
    DEFAULT_SSH_PORT,
    DEFAULT_SSH_USER,
    DOMAIN,
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
