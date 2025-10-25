"""Test the Stundenplan24 integration."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stundenplan24.const import DOMAIN


async def test_setup_unload_entry(hass, mock_config_entry):
    """Test setup and unload (tests close() fix)."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock client with filter objects
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={})
        mock_mobil.fetch_plan = AsyncMock(return_value=None)
        mock_mobil.request_executor = MagicMock()
        mock_mobil.request_executor.shutdown = MagicMock()

        mock_subst = MagicMock()
        mock_subst.fetch_plan = AsyncMock(return_value=None)
        mock_subst.request_executor = MagicMock()
        mock_subst.request_executor.shutdown = MagicMock()

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            [mock_subst]
        )
        client_instance.close = AsyncMock()

        # Test setup
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Test unload (should call close() without errors)
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify client close was called (may be called multiple times during updates)
        assert client_instance.close.called


async def test_setup_entry_coordinator_first_refresh(hass, mock_config_entry):
    """Test that coordinator runs first refresh on setup."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock clients
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={
            "PlanKl20250125.xml": "datetime_object"
        })
        mock_mobil.fetch_plan = AsyncMock(return_value=MagicMock(date="2025-01-25"))
        mock_mobil.request_executor = MagicMock()

        mock_subst = MagicMock()
        mock_subst.fetch_plan = AsyncMock(return_value=MagicMock(date="2025-01-25"))
        mock_subst.request_executor = MagicMock()

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            [mock_subst]
        )
        client_instance.close = AsyncMock()

        # Test setup
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify data was fetched
        assert DOMAIN in hass.data
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert coordinator.data is not None

        # Verify methods were called (filter -> list conversion working)
        mock_mobil.fetch_dates.assert_called()
        mock_mobil.fetch_plan.assert_called()
        mock_subst.fetch_plan.assert_called()


async def test_reload_entry(hass, mock_config_entry):
    """Test reloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock client
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={})
        mock_mobil.fetch_plan = AsyncMock(return_value=None)
        mock_mobil.request_executor = MagicMock()
        mock_mobil.request_executor.shutdown = MagicMock()

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

        # Setup
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Reload
        assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
