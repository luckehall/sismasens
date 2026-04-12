"""Coordinator SISMASENS: ascolta eventi ESPHome e pubblica su cloud MQTT."""
from __future__ import annotations

import json
import logging
import re
import ssl
import threading
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    CONF_DEVICE_PREFIX,
    CONF_CLOUD_TOKEN,
    CONF_CLOUD_ENABLED,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CLOUD_BROKER,
    CLOUD_PORT,
    CLOUD_TOPIC_EVENTS,
    ESPHOME_ENTITIES,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_prefix(prefix: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", prefix.lower())


class SismasensCoordinator(DataUpdateCoordinator):
    """Coordinatore che ascolta i state change delle entità ESPHome del sensore."""

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self._config_entry = config_entry
        self._prefix: str = config_entry.data[CONF_DEVICE_PREFIX]
        self._norm_prefix: str = _normalize_prefix(self._prefix)
        self._cloud_enabled: bool = config_entry.data.get(CONF_CLOUD_ENABLED, False)
        self._cloud_token: str = config_entry.data.get(CONF_CLOUD_TOKEN, "")
        # Coordinate statiche configurate al setup — non cambiano a runtime
        self._lat: float | None = config_entry.data.get(CONF_LATITUDE)
        self._lon: float | None = config_entry.data.get(CONF_LONGITUDE)

        self._mqtt_client = None
        self._unsub_state_listener = None

        # Stato corrente del sensore
        self.data: dict[str, Any] = {
            "earthquake": False,
            "collapse": False,
            "shutoff": False,
            "last_si": 0.0,
            "last_pga": 0.0,
            "last_temp": 0.0,
            "last_mag": 0.0,
            "inst_si": 0.0,
            "inst_pga": 0.0,
            "inst_mag": 0.0,
            "location": "",
            "last_eartquake": None,
            "fw_version": None,
            "power_supply": None,
            "last_event_time": None,
        }

    def _entity_id(self, key: str) -> str:
        return ESPHOME_ENTITIES[key].format(prefix=self._norm_prefix)

    async def async_setup(self) -> None:
        """Avvia il listener sugli state change ESPHome."""
        entity_ids = [self._entity_id(k) for k in ESPHOME_ENTITIES]
        self._unsub_state_listener = async_track_state_change_event(
            self.hass, entity_ids, self._handle_state_change
        )
        _LOGGER.info("SISMASENS coordinator attivo per device '%s'", self._prefix)

        if self._cloud_enabled and self._cloud_token:
            await self.hass.async_add_executor_job(self._connect_mqtt)

    async def async_shutdown(self) -> None:
        """Ferma listener e disconnette MQTT."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
        if self._mqtt_client:
            await self.hass.async_add_executor_job(self._disconnect_mqtt)

    # ------------------------------------------------------------------
    # State change handler
    # ------------------------------------------------------------------

    @callback
    def _handle_state_change(self, event) -> None:
        """Chiamato da HA ogni volta che un'entità ESPHome cambia stato."""
        entity_id: str = event.data["entity_id"]
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None:
            return

        self._sync_state(entity_id, new_state)

        # Rileva fine terremoto: binary_sensor earthquake passa da on → off
        earthquake_entity = self._entity_id("earthquake")
        if (
            entity_id == earthquake_entity
            and old_state is not None
            and old_state.state == "on"
            and new_state.state == "off"
        ):
            _LOGGER.info("SISMASENS: terremoto terminato, raccolta dati evento")
            self.data["last_event_time"] = datetime.now(timezone.utc).isoformat()
            self.async_set_updated_data(dict(self.data))

            if self._cloud_enabled and self._mqtt_client:
                self.hass.async_add_executor_job(self._publish_event)
        else:
            self.async_set_updated_data(dict(self.data))

    def _sync_state(self, entity_id: str, state) -> None:
        """Aggiorna self.data con il nuovo valore dell'entità."""
        try:
            val = state.state
            if val in ("unknown", "unavailable"):
                return
            if entity_id == self._entity_id("earthquake"):
                self.data["earthquake"] = val == "on"
            elif entity_id == self._entity_id("collapse"):
                self.data["collapse"] = val == "on"
            elif entity_id == self._entity_id("shutoff"):
                self.data["shutoff"] = val == "on"
            elif entity_id == self._entity_id("last_si"):
                self.data["last_si"] = float(val)
            elif entity_id == self._entity_id("last_pga"):
                self.data["last_pga"] = float(val)
            elif entity_id == self._entity_id("last_temp"):
                self.data["last_temp"] = float(val)
            elif entity_id == self._entity_id("last_mag"):
                self.data["last_mag"] = float(val)
            elif entity_id == self._entity_id("inst_si"):
                self.data["inst_si"] = float(val)
            elif entity_id == self._entity_id("inst_pga"):
                self.data["inst_pga"] = float(val)
            elif entity_id == self._entity_id("inst_mag"):
                self.data["inst_mag"] = float(val)
            elif entity_id == self._entity_id("location"):
                self.data["location"] = val
            elif entity_id == self._entity_id("last_eartquake"):
                self.data["last_eartquake"] = val
            elif entity_id == self._entity_id("fw_version"):
                self.data["fw_version"] = val
            elif entity_id == self._entity_id("power_supply"):
                self.data["power_supply"] = val
        except (ValueError, AttributeError):
            pass

    # ------------------------------------------------------------------
    # MQTT cloud
    # ------------------------------------------------------------------

    def _connect_mqtt(self) -> None:
        """Connette al broker MQTT cloud (blocca su thread executor)."""
        try:
            import paho.mqtt.client as mqtt

            client = mqtt.Client(client_id=f"ha-sismasens-{self._norm_prefix}")
            client.username_pw_set(
                username=self._norm_prefix,
                password=self._cloud_token,
            )
            tls_ctx = ssl.create_default_context()
            client.tls_set_context(tls_ctx)
            client.connect(CLOUD_BROKER, CLOUD_PORT, keepalive=60)
            client.loop_start()
            self._mqtt_client = client
            _LOGGER.info("SISMASENS: connesso al broker cloud %s", CLOUD_BROKER)
        except Exception as err:
            _LOGGER.error("SISMASENS: errore connessione MQTT cloud: %s", err)

    def _disconnect_mqtt(self) -> None:
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
            self._mqtt_client = None

    def _publish_event(self) -> None:
        """Pubblica evento sismico sul broker cloud."""
        if not self._mqtt_client:
            return

        payload = {
            "sensor_id": self._prefix,
            "timestamp": self.data.get("last_event_time"),
            "lat": self._lat,
            "lon": self._lon,
            "location": self.data.get("location", ""),
            "si": self.data.get("last_si", 0.0),
            "pga": self.data.get("last_pga", 0.0),
            "magnitude": self.data.get("last_mag", 0.0),
            "temp": self.data.get("last_temp", 0.0),
            "collapse": self.data.get("collapse", False),
            "shutoff": self.data.get("shutoff", False),
        }

        topic = CLOUD_TOPIC_EVENTS.format(sensor_id=self._prefix)
        try:
            self._mqtt_client.publish(
                topic,
                json.dumps(payload),
                qos=1,
                retain=False,
            )
            _LOGGER.info("SISMASENS: evento pubblicato su %s: %s", topic, payload)
        except Exception as err:
            _LOGGER.error("SISMASENS: errore pubblicazione MQTT: %s", err)
