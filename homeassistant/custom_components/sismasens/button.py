"""Button SISMASENS: Clear Sensor, Set (hard reset D7S), Reboot."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VERSION, ESPHOME_BUTTONS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    import re
    prefix = entry.data["device_prefix"]
    norm = re.sub(r"[^a-z0-9]", "_", prefix.lower())

    async_add_entities([
        SismasensButton(prefix, norm, "clear_sensor", "Clear Sensor",  "mdi:delete-sweep"),
        SismasensButton(prefix, norm, "set",          "Set (D7S Reset)", "mdi:cog"),
        SismasensButton(prefix, norm, "reboot",       "Reboot",         "mdi:restart"),
    ])


class SismasensButton(ButtonEntity):
    """Pulsante che chiama il corrispondente button ESPHome tramite il servizio HA."""

    def __init__(
        self,
        prefix: str,
        norm_prefix: str,
        action: str,
        name: str,
        icon: str,
    ) -> None:
        self._prefix = prefix
        self._norm_prefix = norm_prefix
        self._action = action
        self._attr_name = f"SISMASENS {prefix} {name}"
        self._attr_unique_id = f"sismasens_{norm_prefix}_btn_{action}"
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, prefix)},
            name=f"SISMASENS {prefix}",
            manufacturer="SISMASENS",
            model="D7S Seismic Sensor",
            sw_version=VERSION,
        )

    async def async_press(self) -> None:
        """Chiama il button ESPHome corrispondente tramite il servizio button.press."""
        template = ESPHOME_BUTTONS.get(self._action)
        entity_id = template.format(prefix=self._norm_prefix) if template else None
        if entity_id is None:
            return

        if self.hass.states.get(entity_id) is None:
            _LOGGER.warning("SISMASENS: entità button '%s' non trovata in HA", entity_id)
            return

        await self.hass.services.async_call(
            "button",
            "press",
            {"entity_id": entity_id},
            blocking=True,
        )
        _LOGGER.debug("SISMASENS: button '%s' premuto", entity_id)
