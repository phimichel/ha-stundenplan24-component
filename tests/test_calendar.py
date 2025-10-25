"""Test the Stundenplan24 calendar platform."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, time, timedelta

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

        # Get events for the week
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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

        # Get events
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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

        # Get events for tomorrow only
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        day_after = tomorrow + timedelta(days=1)

        events = await calendar.async_get_events(hass, tomorrow, day_after)

        # All events should be within the requested range
        for event in events:
            assert event.start >= tomorrow
            assert event.start < day_after
