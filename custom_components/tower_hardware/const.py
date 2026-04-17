# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
DOMAIN = "tower_hardware"

CONF_SSH_HOST = "ssh_host"
CONF_SSH_PORT = "ssh_port"
CONF_SSH_USER = "ssh_user"
CONF_SSH_KEY_PATH = "ssh_key_path"
CONF_SSH_KNOWN_HOSTS = "ssh_known_hosts"
CONF_LED_BINARY = "led_binary"
CONF_OLED_BINARY = "oled_binary"
CONF_FAN_BINARY = "fan_binary"

DEFAULT_SSH_HOST = "127.0.0.1"
DEFAULT_SSH_PORT = 22222
DEFAULT_SSH_USER = "root"
DEFAULT_SSH_KEY_PATH = "/config/.ssh/id_ed25519"
DEFAULT_SSH_KNOWN_HOSTS = "/config/.ssh/known_hosts"
DEFAULT_LED_BINARY = "/mnt/data/supervisor/share/tower_control/tower_ledctl"
DEFAULT_OLED_BINARY = "/mnt/data/supervisor/share/tower_control/tower_oledctl"
DEFAULT_FAN_BINARY = "/mnt/data/supervisor/share/tower_control/tower_fanctl"

PLATFORMS = ["light", "text", "binary_sensor", "sensor", "fan", "number"]
