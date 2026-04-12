"""Binary sensor SISMASENS: earthquake, collapse, shutoff."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import SismasensCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SismasensCoordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = entry.data["device_prefix"]

    async_add_entities([
        SismasensBinarySensor(coordinator, prefix, "earthquake", "Earthquake", BinarySensorDeviceClass.VIBRATION),
        SismasensBinarySensor(coordinator, prefix, "collapse",   "Collapse",   BinarySensorDeviceClass.PROBLEM),
        SismasensBinarySensor(coordinator, prefix, "shutoff",    "Shutoff",    BinarySensorDeviceClass.SAFETY),
    ])


class SismasensBinarySensor(CoordinatorEntity, BinarySensorEntity):

    def __init__(
        self,
        coordinator: SismasensCoordinator,
        prefix: str,
        data_key: str,
        name: str,
        device_class: BinarySensorDeviceClass,
    ) -> None:
        import re
        super().__init__(coordinator)
        norm_prefix = re.sub(r"[^a-z0-9]", "_", prefix.lower())
        self._data_key = data_key
        self._attr_name = f"SISMASENS {prefix} {name}"
        self._attr_unique_id = f"sismasens_{norm_prefix}_{data_key}"
        self._attr_device_class = device_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, prefix)},
            name=f"SISMASENS {prefix}",
            manufacturer="SISMASENS",
            model="D7S Seismic Sensor",
            sw_version=VERSION,
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get(self._data_key, False))
