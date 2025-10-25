"""Test the Stundenplan24 config flow."""
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant import config_entries, data_entry_flow
import aiohttp

from custom_components.stundenplan24.const import DOMAIN
from custom_components.stundenplan24.config_flow import CannotConnect, InvalidAuth


async def test_form_initial(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}


async def test_form_with_mobil_clients(hass, mock_indiware_client_with_mobil, mock_hosting):
    """Test config flow with mobil clients (filter -> list conversion)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "school_url": "https://test.stundenplan24.de",
            "username": "testuser",
            "password": "testpass",
        },
    )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "https://test.stundenplan24.de"
    assert result2["data"] == {
        "school_url": "https://test.stundenplan24.de",
        "username": "testuser",
        "password": "testpass",
    }

    # Verify that the client was properly closed
    mock_indiware_client_with_mobil.return_value.close.assert_called_once()


async def test_form_with_substitution_clients(hass, mock_indiware_client_with_substitution, mock_hosting):
    """Test config flow with substitution clients (filter -> list conversion)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "school_url": "https://test.stundenplan24.de",
            "username": "testuser",
            "password": "testpass",
        },
    )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "https://test.stundenplan24.de"

    # Verify that the client was properly closed
    mock_indiware_client_with_substitution.return_value.close.assert_called_once()


async def test_form_no_clients_available(hass, mock_indiware_client_empty, mock_hosting):
    """Test we show error when no clients are available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "school_url": "https://test.stundenplan24.de",
            "username": "testuser",
            "password": "testpass",
        },
    )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth(hass, mock_hosting):
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Setup mock to raise ClientResponseError with 401
        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates.side_effect = aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=401,
        )

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            []
        )
        client_instance.close = AsyncMock()

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "wrongpass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass, mock_hosting):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Setup mock to raise ClientError
        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates.side_effect = aiohttp.ClientError("Connection timeout")

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            []
        )
        client_instance.close = AsyncMock()

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "testpass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unexpected_exception(hass, mock_hosting):
    """Test we handle unexpected exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Setup mock to raise unexpected exception
        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates.side_effect = Exception("Unexpected error")

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            []
        )
        client_instance.close = AsyncMock()

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "testpass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
