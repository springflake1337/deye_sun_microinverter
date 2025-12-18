"""Config flow for Deye SUN Inverter integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=3600)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    url = f"http://{data[CONF_HOST]}/status.html"
    
    try:
        auth = aiohttp.BasicAuth(data[CONF_USERNAME], data[CONF_PASSWORD])
        async with session.get(url, auth=auth, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 401:
                raise InvalidAuth
            if response.status != 200:
                raise CannotConnect
            
            html = await response.text()
            if "webdata_now_p" not in html:
                raise CannotConnect("Could not find expected data in response")
                
    except aiohttp.ClientError as err:
        _LOGGER.error("Connection error: %s", err)
        raise CannotConnect from err

    return {"title": f"Deye Inverter ({data[CONF_HOST]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deye SUN Inverter."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Deye SUN Inverter."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate connection with new credentials if changed
            test_data = {
                CONF_HOST: self.config_entry.data[CONF_HOST],
                CONF_USERNAME: user_input.get(CONF_USERNAME, self.config_entry.data[CONF_USERNAME]),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD, self.config_entry.data[CONF_PASSWORD]),
            }
            
            try:
                await validate_input(self.hass, test_data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Update both data and options
                new_data = {**self.config_entry.data, **user_input}
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                )
                return self.async_create_entry(title="", data={})

        # Get current values
        current_username = self.config_entry.data.get(CONF_USERNAME, DEFAULT_USERNAME)
        current_password = self.config_entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)
        current_interval = self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        options_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=current_username): str,
                vol.Required(CONF_PASSWORD, default=current_password): str,
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=3600)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
