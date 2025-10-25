"""Test the Stundenplan24 coordinator."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.stundenplan24.coordinator import Stundenplan24Coordinator
from custom_components.stundenplan24.const import DOMAIN, CONF_FORM


async def test_coordinator_filter_to_list_conversion(hass, mock_config_entry):
    """Test that coordinator converts filter objects to lists in update."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock clients with filter objects
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={
            "PlanKl20250125.xml": datetime.now()
        })
        mock_mobil.fetch_plan = AsyncMock(return_value=MagicMock(date=datetime.now().date()))

        mock_subst = MagicMock()
        today_plan = MagicMock()
        today_plan.date = datetime.now().date()
        mock_subst.fetch_plan = AsyncMock(return_value=today_plan)

        client_instance = mock_client.return_value
        # Return filter objects like the real API does
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            [mock_subst]
        )
        client_instance.close = AsyncMock()

        # Create coordinator
        coordinator = Stundenplan24Coordinator(hass, mock_config_entry)

        # Trigger update
        await coordinator.async_refresh()

        # Verify that data was fetched successfully (means list conversion worked)
        assert coordinator.data is not None
        assert "timetable" in coordinator.data
        assert "substitution_today" in coordinator.data

        # Verify methods were called (proves filter -> list -> [0] worked)
        mock_mobil.fetch_dates.assert_called()
        mock_mobil.fetch_plan.assert_called()
        mock_subst.fetch_plan.assert_called()


async def test_coordinator_fetch_substitution_plans(hass, mock_config_entry):
    """Test fetching substitution plan data."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock substitution client
        mock_subst = MagicMock()
        today_plan = MagicMock()
        today_plan.date = datetime.now().date()
        tomorrow_plan = MagicMock()
        tomorrow_plan.date = (datetime.now() + timedelta(days=1)).date()

        mock_subst.fetch_plan = AsyncMock(side_effect=[today_plan, tomorrow_plan])

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(lambda x: x is not None, [])
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            [mock_subst]
        )
        client_instance.close = AsyncMock()

        # Create coordinator
        coordinator = Stundenplan24Coordinator(hass, mock_config_entry)
        await coordinator.async_refresh()

        # Verify data structure
        assert coordinator.data["substitution_today"] == today_plan
        assert coordinator.data["substitution_tomorrow"] == tomorrow_plan

        # Verify fetch_plan was called twice (today and tomorrow)
        assert mock_subst.fetch_plan.call_count == 2


async def test_coordinator_fetch_mobil_plans(hass, mock_config_entry):
    """Test fetching mobil plan data with available_dates dict access."""
    mock_config_entry.add_to_hass(hass)

    # Create sample XML
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
  <Kopf>
    <planart>1</planart>
    <zeitstempel>25.01.2025, 08:00</zeitstempel>
    <DatumPlan>Samstag, 25. Januar 2025</DatumPlan>
    <datei>PlanKl20250125.xml</datei>
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
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock mobil client
        mock_mobil = MagicMock()
        available_dates = {
            "PlanKl20250125.xml": datetime.now(),
            "PlanKl20250124.xml": datetime.now() - timedelta(days=1),
        }

        mock_plan_response = MagicMock()
        mock_plan_response.content = xml_content

        mock_mobil.fetch_dates = AsyncMock(return_value=available_dates)
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_plan_response)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Create coordinator
        coordinator = Stundenplan24Coordinator(hass, mock_config_entry)
        await coordinator.async_refresh()

        # Verify data structure - should be parsed IndiwareMobilPlan
        assert coordinator.data["timetable"] is not None
        assert len(coordinator.data["timetable"].forms) == 1
        assert coordinator.data["timetable"].forms[0].short_name == "5a"

        # Verify fetch_dates was called
        mock_mobil.fetch_dates.assert_called_once()

        # Verify fetch_plan was called with first key from dict
        mock_mobil.fetch_plan.assert_called_once()
        call_args = mock_mobil.fetch_plan.call_args
        assert call_args[1]["date_or_filename"] in available_dates.keys()


async def test_coordinator_handle_api_errors_gracefully(hass, mock_config_entry):
    """Test handling of API errors doesn't crash coordinator."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock client that raises exception
        mock_subst = MagicMock()
        mock_subst.fetch_plan = AsyncMock(side_effect=Exception("API Error"))

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(lambda x: x is not None, [])
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            [mock_subst]
        )
        client_instance.close = AsyncMock()

        # Create coordinator
        coordinator = Stundenplan24Coordinator(hass, mock_config_entry)

        # Should handle error gracefully and set None values
        await coordinator.async_refresh()

        # Data should be present but with None values for failed fetches
        assert coordinator.data is not None
        assert coordinator.data["substitution_today"] is None
        assert coordinator.data["substitution_tomorrow"] is None


async def test_coordinator_no_available_dates(hass, mock_config_entry):
    """Test handling when no timetable files are available."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock mobil client with empty dates
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={})

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Create coordinator
        coordinator = Stundenplan24Coordinator(hass, mock_config_entry)
        await coordinator.async_refresh()

        # Timetable should be None when no dates available
        assert coordinator.data["timetable"] is None
        mock_mobil.fetch_dates.assert_called_once()


async def test_coordinator_parses_mobil_plan_xml(hass, mock_config_entry):
    """Test that coordinator parses IndiwareMobil XML and extracts forms."""
    mock_config_entry.add_to_hass(hass)

    # Create sample XML
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
  <Kopf>
    <planart>1</planart>
    <zeitstempel>25.01.2025, 08:00</zeitstempel>
    <DatumPlan>Samstag, 25. Januar 2025</DatumPlan>
    <datei>PlanKl20250125.xml</datei>
    <woche>4</woche>
    <tageprowoche>5</tageprowoche>
  </Kopf>
  <Klassen>
    <Kl>
      <Kurz>5a</Kurz>
      <KlStunden>
        <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
      </KlStunden>
      <Kurse />
      <Unterricht />
      <Pl>
        <Std>
          <St>1</St>
          <Beginn>08:00</Beginn>
          <Ende>08:45</Ende>
          <Fa FaAe="">Ma</Fa>
          <Le LeAe="">Müller</Le>
          <Ra RaAe="">101</Ra>
          <If></If>
        </Std>
      </Pl>
      <Klausuren />
      <Aufsichten />
    </Kl>
    <Kl>
      <Kurz>10b</Kurz>
      <KlStunden>
        <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
      </KlStunden>
      <Kurse />
      <Unterricht />
      <Pl>
        <Std>
          <St>1</St>
          <Beginn>08:00</Beginn>
          <Ende>08:45</Ende>
          <Fa FaAe="">De</Fa>
          <Le LeAe="">Schmidt</Le>
          <Ra RaAe="">202</Ra>
          <If></If>
        </Std>
      </Pl>
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock mobil client
        mock_mobil = MagicMock()
        available_dates = {"PlanKl20250125.xml": datetime.now()}

        mock_plan_response = MagicMock()
        mock_plan_response.content = xml_content

        mock_mobil.fetch_dates = AsyncMock(return_value=available_dates)
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_plan_response)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Create coordinator
        coordinator = Stundenplan24Coordinator(hass, mock_config_entry)
        await coordinator.async_refresh()

        # Verify data structure - should be parsed IndiwareMobilPlan
        assert coordinator.data["timetable"] is not None
        timetable = coordinator.data["timetable"]

        # Should have 2 forms
        assert len(timetable.forms) == 2
        assert timetable.forms[0].short_name == "5a"
        assert timetable.forms[1].short_name == "10b"


async def test_coordinator_filters_selected_form(hass, mock_config_entry):
    """Test that coordinator filters timetable to selected form only."""
    # Set selected form in options
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={CONF_FORM: "5a"}
    )

    # Create sample XML (same as above)
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
  <Kopf>
    <planart>1</planart>
    <zeitstempel>25.01.2025, 08:00</zeitstempel>
    <DatumPlan>Samstag, 25. Januar 2025</DatumPlan>
    <datei>PlanKl20250125.xml</datei>
    <woche>4</woche>
    <tageprowoche>5</tageprowoche>
  </Kopf>
  <Klassen>
    <Kl>
      <Kurz>5a</Kurz>
      <KlStunden>
        <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
      </KlStunden>
      <Kurse />
      <Unterricht />
      <Pl>
        <Std>
          <St>1</St>
          <Beginn>08:00</Beginn>
          <Ende>08:45</Ende>
          <Fa FaAe="">Ma</Fa>
          <Le LeAe="">Müller</Le>
          <Ra RaAe="">101</Ra>
          <If></If>
        </Std>
      </Pl>
      <Klausuren />
      <Aufsichten />
    </Kl>
    <Kl>
      <Kurz>10b</Kurz>
      <KlStunden />
      <Kurse />
      <Unterricht />
      <Pl />
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ) as mock_hosting:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting.deserialize.return_value = mock_hosting_instance

        # Mock mobil client
        mock_mobil = MagicMock()
        available_dates = {"PlanKl20250125.xml": datetime.now()}

        mock_plan_response = MagicMock()
        mock_plan_response.content = xml_content

        mock_mobil.fetch_dates = AsyncMock(return_value=available_dates)
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_plan_response)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Create coordinator
        coordinator = Stundenplan24Coordinator(hass, mock_config_entry)
        await coordinator.async_refresh()

        # Verify data structure - should only contain selected form
        assert coordinator.data["timetable"] is not None
        timetable = coordinator.data["timetable"]

        # Should only have form 5a
        assert len(timetable.forms) == 1
        assert timetable.forms[0].short_name == "5a"
