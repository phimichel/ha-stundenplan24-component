"""Config flow for Stundenplan24 integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from stundenplan24_py.client import IndiwareStundenplanerClient
from stundenplan24_py.endpoints import Hosting, Credentials
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_PASSWORD,
    CONF_SCHOOL_URL,
    CONF_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCHOOL_URL): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)

    # Create credentials
    credentials = Credentials(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
    )

    # Create hosting object
    hosting = Hosting(
        url=data[CONF_SCHOOL_URL],
        credentials=credentials,
    )

    # Try to create client and fetch data
    try:
        client = IndiwareStundenplanerClient(
            hosting=hosting,
            session=session,
        )

        # Try to fetch available dates to validate connection
        if client.indiware_mobil_clients:
            await client.indiware_mobil_clients[0].fetch_dates()
        elif client.substitution_plan_clients:
            # Try substitution plan if no mobil client available
            await client.substitution_plan_clients[0].get_metadata()
        else:
            raise CannotConnect("No clients available")

        await client.close()

    except aiohttp.ClientResponseError as err:
        if err.status == 401:
            raise InvalidAuth from err
        raise CannotConnect from err
    except aiohttp.ClientError as err:
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during validation")
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": data[CONF_SCHOOL_URL]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stundenplan24."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
