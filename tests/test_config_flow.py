"""Test the Stundenplan24 config flow."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from homeassistant import config_entries, data_entry_flow
import aiohttp

from custom_components.stundenplan24.const import DOMAIN, CONF_FORM
from custom_components.stundenplan24.config_flow import CannotConnect, InvalidAuth


async def test_form_initial(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}


async def test_form_with_mobil_clients(hass, mock_hosting, mock_indiware_mobil_plan):
    """Test config flow with two-step form selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    # Sample XML with forms
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
    <Kopf>
        <planart>Klasse</planart>
        <zeitstempel>25.01.2025, 08:00</zeitstempel>
        <DatumPlan>Samstag, 25. Januar 2025</DatumPlan>
        <datei>PlanKl20250125.xml</datei>
        <woche>4</woche>
    </Kopf>
    <Klassen>
        <Kl>
            <Kurz>5a</Kurz>
            <KlStunden>
                <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
            </KlStunden>
            <Pl></Pl>
        </Kl>
        <Kl>
            <Kurz>5b</Kurz>
            <KlStunden>
                <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
            </KlStunden>
            <Pl></Pl>
        </Kl>
    </Klassen>
</VpMobil>"""

    # Mock client for both validation and form fetching
    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.config_flow.Hosting"
    ) as mock_hosting_cls:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting_cls.deserialize.return_value = mock_hosting_instance

        # Create mock response object with content attribute
        mock_response = MagicMock()
        mock_response.content = sample_xml

        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={"PlanKl20250125.xml": "2025-01-25"})
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_response)

        client_instance = mock_client.return_value
        client_instance.form_plan_client = mock_mobil
        client_instance.indiware_mobil_clients = filter(lambda x: x is not None, [mock_mobil])
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Step 1: Enter credentials
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "testpass",
            },
        )

        # Should now show form selection step
        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "select_form"

        # Step 2: Select form
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_FORM: "5a"},
        )

        assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result3["title"] == "https://test.stundenplan24.de - 5a"
        assert result3["data"] == {
            "school_url": "https://test.stundenplan24.de",
            "username": "testuser",
            "password": "testpass",
            "form": "5a",
        }


async def test_form_with_substitution_clients(hass, mock_indiware_client_with_substitution, mock_hosting):
    """Test config flow with substitution clients only (no form selection needed)."""
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

    # When only substitution clients available, skip form selection
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "https://test.stundenplan24.de"
    assert result2["data"] == {
        "school_url": "https://test.stundenplan24.de",
        "username": "testuser",
        "password": "testpass",
    }

    # Verify that the client was properly closed (may be called multiple times during setup)
    assert mock_indiware_client_with_substitution.return_value.close.called


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


# Options Flow Tests removed - form selection moved to config flow
