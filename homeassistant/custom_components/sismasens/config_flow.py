"""Config flow per l'integrazione SISMASENS."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_DEVICE_PREFIX,
    CONF_CLOUD_TOKEN,
    CONF_CLOUD_ENABLED,
    ESPHOME_ENTITIES,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_prefix(prefix: str) -> str:
    """Normalizza il prefisso: 'mi-001' → 'mi_001' (come fa HA con i nomi entità)."""
    return re.sub(r"[^a-z0-9]", "_", prefix.lower())


def _check_esphome_entities(hass: HomeAssistant, prefix: str) -> list[str]:
    """Verifica quali entità ESPHome esistono già in HA. Restituisce quelle mancanti."""
    norm = _normalize_prefix(prefix)
    missing = []
    for key, template in ESPHOME_ENTITIES.items():
        entity_id = template.format(prefix=norm)
        if hass.states.get(entity_id) is None:
            missing.append(entity_id)
    return missing


class SismasensConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow SISMASENS in due step: device + cloud opzionale."""

    VERSION = 1

    def __init__(self) -> None:
        self._device_prefix: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: inserimento prefisso device ESPHome."""
        errors: dict[str, str] = {}

        if user_input is not None:
            prefix = user_input[CONF_DEVICE_PREFIX].strip()
            norm = _normalize_prefix(prefix)

            # Impedisce config entry duplicate per lo stesso device
            await self.async_set_unique_id(norm)
            self._abort_if_unique_id_configured()

            missing = _check_esphome_entities(self.hass, prefix)

            # Richiediamo almeno l'entità earthquake
            earthquake_entity = ESPHOME_ENTITIES["earthquake"].format(prefix=norm)
            if self.hass.states.get(earthquake_entity) is None:
                errors[CONF_DEVICE_PREFIX] = "device_not_found"
            else:
                if missing:
                    _LOGGER.warning("SISMASENS: entità mancanti per '%s': %s", prefix, missing)
                self._device_prefix = prefix
                return await self.async_step_cloud()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_PREFIX, description={"suggested_value": "mi-001"}): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "example": "mi-001",
                "doc_url": "https://github.com/luckehall/sismasens",
            },
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2 (opzionale): configurazione pubblicazione cloud."""
        errors: dict[str, str] = {}

        if user_input is not None:
            cloud_enabled = user_input.get(CONF_CLOUD_ENABLED, False)
            cloud_token = user_input.get(CONF_CLOUD_TOKEN, "").strip()

            if cloud_enabled and not cloud_token:
                errors[CONF_CLOUD_TOKEN] = "token_required"
            else:
                return self.async_create_entry(
                    title=f"SISMASENS {self._device_prefix}",
                    data={
                        CONF_DEVICE_PREFIX: self._device_prefix,
                        CONF_CLOUD_ENABLED: cloud_enabled,
                        CONF_CLOUD_TOKEN: cloud_token,
                    },
                )

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CLOUD_ENABLED, default=False): bool,
                    vol.Optional(CONF_CLOUD_TOKEN, default=""): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "register_url": "https://sismasens.iotzator.com/register",
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SismasensOptionsFlow:
        return SismasensOptionsFlow(config_entry)


class SismasensOptionsFlow(config_entries.OptionsFlow):
    """Permette di modificare token e cloud enable dopo il setup iniziale."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._current = {**config_entry.data, **config_entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CLOUD_ENABLED,
                        default=self._current.get(CONF_CLOUD_ENABLED, False),
                    ): bool,
                    vol.Optional(
                        CONF_CLOUD_TOKEN,
                        default=self._current.get(CONF_CLOUD_TOKEN, ""),
                    ): str,
                }
            ),
        )
