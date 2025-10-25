"""Config flow for Stundenplan24 integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from .stundenplan24_py.client import IndiwareStundenplanerClient, Hosting
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_FORM,
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
    # Create hosting object using deserialize method
    hosting = Hosting.deserialize({
        "creds": {
            "username": data[CONF_USERNAME],
            "password": data[CONF_PASSWORD],
        },
        "endpoints": data[CONF_SCHOOL_URL],
    })

    # Try to create client and fetch data
    try:
        client = IndiwareStundenplanerClient(hosting=hosting)

        # Try to fetch available dates to validate connection
        mobil_clients = list(client.indiware_mobil_clients)
        substitution_clients = list(client.substitution_plan_clients)

        if mobil_clients:
            await mobil_clients[0].fetch_dates()
        elif substitution_clients:
            # Try substitution plan if no mobil client available
            await substitution_clients[0].get_metadata()
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

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)

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


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Stundenplan24."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Load available forms from API
        try:
            forms = await self._get_available_forms()
        except CannotConnect:
            errors["base"] = "cannot_connect"
            forms = []
        except NoFormClient:
            errors["base"] = "no_form_client"
            forms = []
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
            forms = []

        # Create schema with form selection
        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FORM,
                    default=self.config_entry.options.get(CONF_FORM, ""),
                ): vol.In(forms) if forms else str,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )

    async def _get_available_forms(self) -> list[str]:
        """Get available forms from the API."""
        # Create hosting object using config entry data
        hosting = Hosting.deserialize({
            "creds": {
                "username": self.config_entry.data[CONF_USERNAME],
                "password": self.config_entry.data[CONF_PASSWORD],
            },
            "endpoints": self.config_entry.data[CONF_SCHOOL_URL],
        })

        client = IndiwareStundenplanerClient(hosting=hosting)

        if client.form_plan_client is None:
            await client.close()
            raise NoFormClient("No form plan client available")

        try:
            # Fetch a plan to get available forms
            plan_response = await client.form_plan_client.fetch_plan()

            # Parse the XML to get forms
            from .stundenplan24_py.indiware_mobil import IndiwareMobilPlan
            import xml.etree.ElementTree as ET

            root = ET.fromstring(plan_response.content)
            plan = IndiwareMobilPlan.from_xml(root)

            forms = [form.short_name for form in plan.forms]
            await client.close()

            return forms
        except Exception as err:
            await client.close()
            raise CannotConnect from err


class NoFormClient(HomeAssistantError):
    """Error to indicate no form client is available."""
