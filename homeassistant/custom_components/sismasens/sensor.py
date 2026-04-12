"""Sensori numerici SISMASENS per Home Assistant."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
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

    entities = [
        SismasensSensor(coordinator, prefix, "last_si",    "Last SI",    "cm/s",  SensorStateClass.MEASUREMENT, SensorDeviceClass.SPEED),
        SismasensSensor(coordinator, prefix, "last_pga",   "Last PGA",   "g",     SensorStateClass.MEASUREMENT, None),
        SismasensSensor(coordinator, prefix, "last_temp",  "Last Temp",  "°C",    SensorStateClass.MEASUREMENT, SensorDeviceClass.TEMPERATURE),
        SismasensSensor(coordinator, prefix, "last_mag",   "Last M",     None,    SensorStateClass.MEASUREMENT, None),
        SismasensSensor(coordinator, prefix, "inst_si",    "Inst SI",    "cm/s",  SensorStateClass.MEASUREMENT, SensorDeviceClass.SPEED),
        SismasensSensor(coordinator, prefix, "inst_pga",   "Inst PGA",   "g",     SensorStateClass.MEASUREMENT, None),
        SismasensSensor(coordinator, prefix, "inst_mag",   "Inst M",     None,    SensorStateClass.MEASUREMENT, None),
    ]
    async_add_entities(entities)


class SismasensSensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self,
        coordinator: SismasensCoordinator,
        prefix: str,
        data_key: str,
        name: str,
        unit: str | None,
        state_class: SensorStateClass,
        device_class: SensorDeviceClass | None,
    ) -> None:
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = f"SISMASENS {prefix} {name}"
        self._attr_unique_id = f"sismasens_{prefix}_{data_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_device_class = device_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, prefix)},
            name=f"SISMASENS {prefix}",
            manufacturer="SISMASENS",
            model="D7S Seismic Sensor",
            sw_version=VERSION,
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)
