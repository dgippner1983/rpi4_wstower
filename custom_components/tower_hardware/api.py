# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_FAN_BINARY,
    CONF_LED_BINARY,
    CONF_OLED_BINARY,
    CONF_SSH_HOST,
    CONF_SSH_KEY_PATH,
    CONF_SSH_KNOWN_HOSTS,
    CONF_SSH_PORT,
    CONF_SSH_USER,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class TowerState:
    led_available: bool = False
    oled_available: bool = False
    fan_available: bool = False
    led_is_on: bool = False
    led_r: int = 255
    led_g: int = 228
    led_b: int = 206
    led_brightness: int = 200
    led_effect: str | None = None
    oled_text: str = ""
    cpu_temp: float | None = None
    fan_mode: str = "auto"
    fan_duty: int = 0


class TowerApi:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.state = TowerState()

    def _ssh(self) -> list[str]:
        return [
            "ssh",
            "-i", self.data[CONF_SSH_KEY_PATH],
            "-o", "StrictHostKeyChecking=no",
            "-o", f"UserKnownHostsFile={self.data[CONF_SSH_KNOWN_HOSTS]}",
            "-o", "ControlMaster=auto",
            "-o", "ControlPath=/tmp/tower_ssh_%r@%h:%p",
            "-o", "ControlPersist=60",
            "-p", str(self.data[CONF_SSH_PORT]),
            f"{self.data[CONF_SSH_USER]}@{self.data[CONF_SSH_HOST]}",
        ]

    async def _run(self, command: str) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *self._ssh(),
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=15)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError("SSH command timed out")
        except asyncio.CancelledError:
            proc.kill()
            await proc.wait()
            raise
        return proc.returncode, out.decode().strip(), err.decode().strip()

    async def _check_bin(self, path: str) -> bool:
        rc, _, _ = await self._run(f"test -x {shlex.quote(path)}")
        return rc == 0

    async def _must(self, cmd: str) -> str:
        rc, out, err = await self._run(cmd)
        if rc != 0:
            raise RuntimeError(err or out or f"command failed {rc}")
        return out

    async def probe(self) -> dict[str, Any]:
        self.state.led_available = await self._check_bin(self.data[CONF_LED_BINARY])
        self.state.oled_available = await self._check_bin(self.data[CONF_OLED_BINARY])
        self.state.fan_available = await self._check_bin(self.data[CONF_FAN_BINARY])

        if self.state.led_available:
            state_file = os.path.join(
                os.path.dirname(self.data[CONF_LED_BINARY]), "tower_led_state.json"
            )
            rc, out, _ = await self._run(f"cat {shlex.quote(state_file)}")
            if rc == 0 and out:
                try:
                    st = json.loads(out)
                    self.state.led_is_on = bool(st.get("is_on", False))
                    self.state.led_r = int(st.get("r", 255))
                    self.state.led_g = int(st.get("g", 228))
                    self.state.led_b = int(st.get("b", 206))
                    self.state.led_brightness = int(st.get("brightness", 200))
                    self.state.led_effect = st.get("effect") or None
                except Exception:
                    _LOGGER.warning("LED state file could not be parsed (rc=%d, out=%r)", rc, out)

        rc, out, _ = await self._run("cat /sys/class/thermal/thermal_zone0/temp")
        if rc == 0 and out:
            try:
                self.state.cpu_temp = int(out) / 1000.0
            except ValueError:
                pass

        if self.state.fan_available:
            fan_state_file = os.path.join(
                os.path.dirname(self.data[CONF_FAN_BINARY]), "tower_fan_state.json"
            )
            rc, out, _ = await self._run(f"cat {shlex.quote(fan_state_file)}")
            if rc == 0 and out:
                try:
                    fs = json.loads(out)
                    self.state.fan_mode = fs.get("mode", "auto")
                    self.state.fan_duty = int(fs.get("duty", 0))
                except Exception:
                    _LOGGER.warning("Fan state file could not be parsed: %r", out)

        return {
            "led": {
                "available": self.state.led_available,
                "is_on": self.state.led_is_on,
                "r": self.state.led_r,
                "g": self.state.led_g,
                "b": self.state.led_b,
                "brightness": self.state.led_brightness,
                "effect": self.state.led_effect,
            },
            "oled": {
                "available": self.state.oled_available,
                "last_text": self.state.oled_text,
            },
            "cpu": {
                "temp": self.state.cpu_temp,
            },
            "fan": {
                "available": self.state.fan_available,
                "mode": self.state.fan_mode,
                "duty": self.state.fan_duty,
            },
        }

    async def led_off(self):
        await self._must(f"{shlex.quote(self.data[CONF_LED_BINARY])} off")

    async def led_color(self, r: int, g: int, b: int, brightness: int):
        await self._must(f"{shlex.quote(self.data[CONF_LED_BINARY])} color {r} {g} {b} {brightness}")

    async def led_effect(self, name: str):
        mapping = {
            "Blink Slow": "blink_slow",
            "Blink Fast": "blink_fast",
            "Rainbow": "rainbow",
            "Pulse": "pulse",
        }
        effect = mapping.get(name)
        if not effect:
            raise ValueError(f"Unknown effect: {name!r}")
        await self._must(f"{shlex.quote(self.data[CONF_LED_BINARY])} effect {effect}")

    async def fan_set(self, percentage: int):
        await self._must(f"{shlex.quote(self.data[CONF_FAN_BINARY])} {percentage}")

    async def fan_auto(self):
        await self._must(f"{shlex.quote(self.data[CONF_FAN_BINARY])} auto")

    async def fan_off(self):
        await self._must(f"{shlex.quote(self.data[CONF_FAN_BINARY])} off")

    async def oled_text(self, text: str):
        oled = shlex.quote(self.data[CONF_OLED_BINARY])
        lines = [line.rstrip() for line in text.replace("\\n", "\n").splitlines()]
        lines = [l for l in lines if l != ""]
        if not lines:
            lines = [""]
        if len(lines) == 1:
            await self._must(f"{oled} text {shlex.quote(lines[0][:20])}")
        elif len(lines) == 2:
            await self._must(
                f"{oled} text2 "
                f"{shlex.quote(lines[0][:20])} {shlex.quote(lines[1][:20])}"
            )
        else:
            await self._must(
                f"{oled} text3 "
                f"{shlex.quote(lines[0][:20])} "
                f"{shlex.quote(lines[1][:20])} "
                f"{shlex.quote(lines[2][:20])}"
            )
        self.state.oled_text = "\n".join(lines[:3])
