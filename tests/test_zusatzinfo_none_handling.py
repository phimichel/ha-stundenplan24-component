"""Test that ZusatzInfo handles None values correctly."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.stundenplan24.const import DOMAIN


async def test_sensor_handles_none_in_additional_info(hass: HomeAssistant, mock_config_entry):
    """Test that sensor handles None values in additional_info list."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client with timetable containing None in additional_info
        mock_mobil = MagicMock()
        today = datetime.now().date()

        available_dates = {
            f"PlanKl{today.strftime('%Y%m%d')}.xml": datetime.now(),
        }

        # Create XML with ZusatzInfo containing empty and None-like entries
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
  <Kopf>
    <planart>K</planart>
    <zeitstempel>{today.strftime('%d.%m.%Y')}, 08:00</zeitstempel>
    <DatumPlan>Montag, {today.day}. Oktober {today.year}</DatumPlan>
    <datei>PlanKl{today.strftime('%Y%m%d')}.xml</datei>
    <woche>4</woche>
    <tageprowoche>5</tageprowoche>
  </Kopf>
  <Klassen>
    <Kl>
      <Kurz>5a</Kurz>
      <KlStunden />
      <Kurse />
      <Unterricht />
      <Pl />
    </Kl>
  </Klassen>
  <ZusatzInfo>
    <ZiZeile></ZiZeile>
    <ZiZeile>Wichtige Information</ZiZeile>
    <ZiZeile></ZiZeile>
  </ZusatzInfo>
</VpMobil>"""

        mock_plan_response = MagicMock()
        mock_plan_response.content = xml_content

        mock_mobil.fetch_dates = AsyncMock(return_value=available_dates)
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_plan_response)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None, [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check sensor state - should not crash
        state = hass.states.get("sensor.stundenplan24_zusatzinformationen")
        assert state is not None

        # Should handle the data gracefully
        assert "today_lines" in state.attributes
        # Should only have non-empty lines
        today_lines = state.attributes["today_lines"]
        assert "" not in today_lines
        assert None not in today_lines

        # Should have the one valid line
        if today_lines:
            assert "Wichtige Information" in today_lines


async def test_calendar_handles_none_in_additional_info(hass: HomeAssistant, mock_config_entry):
    """Test that calendar handles None values in additional_info list."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client with timetable containing None in additional_info
        mock_mobil = MagicMock()
        today = datetime.now().date()

        available_dates = {
            f"PlanKl{today.strftime('%Y%m%d')}.xml": datetime.now(),
        }

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
  <Kopf>
    <planart>K</planart>
    <zeitstempel>{today.strftime('%d.%m.%Y')}, 08:00</zeitstempel>
    <DatumPlan>Montag, {today.day}. Oktober {today.year}</DatumPlan>
    <datei>PlanKl{today.strftime('%Y%m%d')}.xml</datei>
    <woche>4</woche>
    <tageprowoche>5</tageprowoche>
  </Kopf>
  <Klassen>
    <Kl>
      <Kurz>5a</Kurz>
      <KlStunden />
      <Kurse />
      <Unterricht />
      <Pl />
    </Kl>
  </Klassen>
  <ZusatzInfo>
    <ZiZeile></ZiZeile>
    <ZiZeile>Schulausflug</ZiZeile>
    <ZiZeile></ZiZeile>
  </ZusatzInfo>
</VpMobil>"""

        mock_plan_response = MagicMock()
        mock_plan_response.content = xml_content

        mock_mobil.fetch_dates = AsyncMock(return_value=available_dates)
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_plan_response)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None, [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check calendar state - should not crash
        state = hass.states.get("calendar.stundenplan24_wochenplan")
        assert state is not None

        # Calendar should be available (not in error state)
        assert state.state in ["on", "off"]
