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

    client = IndiwareStundenplanerClient(hosting=hosting)

    # Try to create client and fetch data
    try:
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

    except aiohttp.ClientResponseError as err:
        if err.status == 401:
            raise InvalidAuth from err
        raise CannotConnect from err
    except aiohttp.ClientError as err:
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during validation")
        raise CannotConnect from err
    finally:
        await client.close()

    # Return info that you want to store in the config entry.
    return {"title": data[CONF_SCHOOL_URL]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stundenplan24."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._credentials: dict[str, Any] = {}
        self._available_forms: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Store credentials for next step
                self._credentials = user_input

                # Check if form_plan_client is available
                try:
                    forms = await self._get_available_forms()
                    if forms:
                        # Proceed to form selection
                        self._available_forms = forms
                        return await self.async_step_select_form()
                except Exception as err:
                    _LOGGER.debug("No form client available: %s", err)

                # No form selection needed, create entry directly
                return self.async_create_entry(
                    title=user_input[CONF_SCHOOL_URL],
                    data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_select_form(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle form (class) selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Combine credentials with form selection
            data = {**self._credentials, **user_input}
            selected_form = user_input[CONF_FORM]

            return self.async_create_entry(
                title=f"{self._credentials[CONF_SCHOOL_URL]} - {selected_form}",
                data=data
            )

        # Show form selection
        schema = vol.Schema({
            vol.Required(CONF_FORM): vol.In(self._available_forms)
        })

        return self.async_show_form(
            step_id="select_form", data_schema=schema, errors=errors
        )

    async def _get_available_forms(self) -> list[str]:
        """Get available forms from the API."""
        hosting = Hosting.deserialize({
            "creds": {
                "username": self._credentials[CONF_USERNAME],
                "password": self._credentials[CONF_PASSWORD],
            },
            "endpoints": self._credentials[CONF_SCHOOL_URL],
        })

        client = IndiwareStundenplanerClient(hosting=hosting)

        try:
            if client.form_plan_client is None:
                return []

            # Fetch a plan to get available forms
            plan_response = await client.form_plan_client.fetch_plan()

            # Parse the XML to get forms
            from .stundenplan24_py.indiware_mobil import IndiwareMobilPlan
            import xml.etree.ElementTree as ET

            root = ET.fromstring(plan_response.content)
            plan = IndiwareMobilPlan.from_xml(root)

            forms = [form.short_name for form in plan.forms]
            return forms
        except Exception as err:
            _LOGGER.exception("Could not fetch forms")
            return []
        finally:
            await client.close()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
