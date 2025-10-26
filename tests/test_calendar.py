"""Test the Stundenplan24 calendar platform."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, date, time, timedelta

from homeassistant.components.calendar import CalendarEvent

from custom_components.stundenplan24.const import DOMAIN


async def test_calendar_setup(hass, mock_config_entry):
    """Test calendar platform setup."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client
        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(lambda x: x is not None, [])
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check calendar entity exists
        state = hass.states.get("calendar.stundenplan24_wochenplan")
        assert state is not None


async def test_calendar_events_from_timetable(hass, mock_config_entry, mock_timetable_with_lessons):
    """Test calendar creates events from timetable lessons."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client with timetable
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={"PlanKl20250125.xml": datetime.now()})
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_timetable_with_lessons)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Get calendar entity
        calendar = hass.data[DOMAIN][mock_config_entry.entry_id]["calendar"]

        # Get events for the week containing the plan date (Jan 25, 2025)
        # The mock fixture has a plan for Saturday, Jan 25, 2025
        plan_date = date(2025, 1, 25)
        start = datetime.combine(plan_date, datetime.min.time())
        end = start + timedelta(days=7)

        events = await calendar.async_get_events(hass, start, end)

        # Should have events from lessons
        assert len(events) > 0

        # Check first event structure
        event = events[0]
        assert isinstance(event, CalendarEvent)
        assert event.summary is not None  # Subject
        assert event.start is not None
        assert event.end is not None
        assert event.description is not None  # Should contain teacher and room


async def test_calendar_event_attributes(hass, mock_config_entry, mock_timetable_with_lessons):
    """Test calendar event includes all lesson attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client with timetable
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={"PlanKl20250125.xml": datetime.now()})
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_timetable_with_lessons)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Get calendar entity
        calendar = hass.data[DOMAIN][mock_config_entry.entry_id]["calendar"]

        # Get events for the week containing the plan date (Jan 25, 2025)
        plan_date = date(2025, 1, 25)
        start = datetime.combine(plan_date, datetime.min.time())
        end = start + timedelta(days=7)
        events = await calendar.async_get_events(hass, start, end)

        # Find math lesson (Ma)
        math_event = next((e for e in events if "Ma" in e.summary), None)
        assert math_event is not None

        # Check attributes in description
        assert "Müller" in math_event.description  # Teacher
        assert "101" in math_event.description  # Room


async def test_calendar_no_timetable(hass, mock_config_entry):
    """Test calendar handles missing timetable gracefully."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client with no timetable
        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(lambda x: x is not None, [])
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Get calendar entity
        calendar = hass.data[DOMAIN][mock_config_entry.entry_id]["calendar"]

        # Get events should return empty list
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        events = await calendar.async_get_events(hass, start, end)

        assert events == []


async def test_calendar_filters_by_date_range(hass, mock_config_entry, mock_timetable_with_lessons):
    """Test calendar only returns events in requested date range."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client with timetable
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={"PlanKl20250125.xml": datetime.now()})
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_timetable_with_lessons)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Get calendar entity
        calendar = hass.data[DOMAIN][mock_config_entry.entry_id]["calendar"]

        # Test date filtering: request day AFTER the plan date (Jan 26)
        # Should return no events since plan is for Jan 25
        plan_date = date(2025, 1, 25)
        day_after_plan = datetime.combine(plan_date + timedelta(days=1), datetime.min.time())
        two_days_after = day_after_plan + timedelta(days=1)

        events = await calendar.async_get_events(hass, day_after_plan, two_days_after)

        # Should have no events since we're requesting a date range AFTER the plan date
        assert len(events) == 0


async def test_calendar_filters_by_subject(hass, mock_config_entry):
    """Test calendar filters events by configured subject filter."""
    # Configure entry with subject filter for only "Ma" and "De"
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={"filter_subjects": ["Ma", "De"]}
    )

    # Mock XML response with multiple subjects
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
        <KlSt ZeitVon="08:50" ZeitBis="09:35">2</KlSt>
        <KlSt ZeitVon="09:55" ZeitBis="10:40">3</KlSt>
        <KlSt ZeitVon="10:45" ZeitBis="11:30">4</KlSt>
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
        <Std>
          <St>2</St>
          <Beginn>08:50</Beginn>
          <Ende>09:35</Ende>
          <Fa FaAe="">De</Fa>
          <Le LeAe="">Schmidt</Le>
          <Ra RaAe="">102</Ra>
          <If></If>
        </Std>
        <Std>
          <St>3</St>
          <Beginn>09:55</Beginn>
          <Ende>10:40</Ende>
          <Fa FaAe="">En</Fa>
          <Le LeAe="">Meyer</Le>
          <Ra RaAe="">103</Ra>
          <If></If>
        </Std>
        <Std>
          <St>4</St>
          <Beginn>10:45</Beginn>
          <Ende>11:30</Ende>
          <Fa FaAe="">Sp</Fa>
          <Le LeAe="">Weber</Le>
          <Ra RaAe="">Turnhalle</Ra>
          <If></If>
        </Std>
      </Pl>
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    plan_response = MagicMock()
    plan_response.content = xml_content

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        # Mock client with timetable
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={"PlanKl20250125.xml": datetime.now()})
        mock_mobil.fetch_plan = AsyncMock(return_value=plan_response)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Setup entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Get calendar entity
        calendar = hass.data[DOMAIN][mock_config_entry.entry_id]["calendar"]

        # Get events for the plan date
        plan_date = date(2025, 1, 25)  # Saturday
        # Request events for the actual plan date
        start_datetime = datetime.combine(plan_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)

        events = await calendar.async_get_events(hass, start_datetime, end_datetime)

    # Should only have Ma and De lessons, not En and Sp
    subjects = [event.summary for event in events]
    assert "Ma" in subjects
    assert "De" in subjects
    assert "En" not in subjects
    assert "Sp" not in subjects


async def test_calendar_no_filter_shows_all_subjects(hass, mock_config_entry):
    """Test calendar shows all subjects when no filter is configured."""
    mock_config_entry.add_to_hass(hass)
    # No filter configured (empty list = show all)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={"filter_subjects": []}
    )

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
        <KlSt ZeitVon="08:50" ZeitBis="09:35">2</KlSt>
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
        <Std>
          <St>2</St>
          <Beginn>08:50</Beginn>
          <Ende>09:35</Ende>
          <Fa FaAe="">En</Fa>
          <Le LeAe="">Meyer</Le>
          <Ra RaAe="">103</Ra>
          <If></If>
        </Std>
      </Pl>
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    plan_response = MagicMock()
    plan_response.content = xml_content

    with patch(
        "custom_components.stundenplan24.coordinator.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.coordinator.Hosting"
    ):
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={"PlanKl20250125.xml": datetime.now()})
        mock_mobil.fetch_plan = AsyncMock(return_value=plan_response)

        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(lambda x: x is not None, [mock_mobil])
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        calendar = hass.data[DOMAIN][mock_config_entry.entry_id]["calendar"]

        plan_date = date(2025, 1, 25)
        start_datetime = datetime.combine(plan_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)

        events = await calendar.async_get_events(hass, start_datetime, end_datetime)

    # Should show all subjects when filter is empty
    subjects = [event.summary for event in events]
    assert "Ma" in subjects
    assert "En" in subjects
