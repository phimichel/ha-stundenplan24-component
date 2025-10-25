"""Calendar platform for Stundenplan24 integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import Stundenplan24Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]

    # Handle both coordinator-only and dict storage
    if isinstance(entry_data, Stundenplan24Coordinator):
        coordinator = entry_data
        # Convert to dict storage for calendar
        hass.data[DOMAIN][config_entry.entry_id] = {"coordinator": coordinator}
        entry_data = hass.data[DOMAIN][config_entry.entry_id]
    else:
        coordinator = entry_data["coordinator"]

    calendar = Stundenplan24Calendar(coordinator)
    async_add_entities([calendar])

    # Store calendar entity for tests
    entry_data["calendar"] = calendar


class Stundenplan24Calendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity for Stundenplan24 timetable."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Stundenplan24Coordinator) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = "Wochenplan"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_calendar"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Stundenplan24",
            "manufacturer": "Stundenplan24",
            "model": "Student Schedule",
            "sw_version": "1.0",
        }

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        now = datetime.now()
        events = self._get_events(now, now + timedelta(days=7))

        if not events:
            return None

        # Find next event
        future_events = [e for e in events if e.start > now]
        if future_events:
            return min(future_events, key=lambda e: e.start)

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events(start_date, end_date)

    def _get_events(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Get calendar events within a datetime range."""
        if not self.coordinator.data:
            return []

        timetable = self.coordinator.data.get("timetable")
        if not timetable or not timetable.forms:
            return []

        # Ensure start_date and end_date are timezone-aware
        if start_date.tzinfo is None:
            start_date = dt_util.as_local(start_date)
        if end_date.tzinfo is None:
            end_date = dt_util.as_local(end_date)

        events = []

        # Get the first form (should be the selected one after filtering)
        form = timetable.forms[0]

        # The timetable contains lessons for a specific week
        # We need to project these lessons onto the requested date range
        # For now, we'll repeat the lessons for each week in the range

        # Calculate the start of the current week
        current_week_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        current_week_start = current_week_start - timedelta(days=current_week_start.weekday())

        # Generate events for each lesson, repeating weekly
        for lesson in form.lessons:
            if not lesson.start or not lesson.end:
                continue

            # Determine the weekday for this lesson (0=Monday, 4=Friday)
            # For now, assume all lessons are distributed across Monday-Friday
            # In reality, this would come from the lesson's day information
            lesson_weekday = lesson.period % 5 if hasattr(lesson, 'period') and lesson.period else 0

            # Project lesson onto each week in the date range
            week_start = current_week_start
            while week_start < end_date:
                lesson_date = week_start + timedelta(days=lesson_weekday)
                # Use dt_util to create timezone-aware datetime
                lesson_datetime = dt_util.start_of_local_day(lesson_date).replace(
                    hour=lesson.start.hour,
                    minute=lesson.start.minute,
                    second=lesson.start.second
                )
                lesson_end_datetime = dt_util.start_of_local_day(lesson_date).replace(
                    hour=lesson.end.hour,
                    minute=lesson.end.minute,
                    second=lesson.end.second
                )

                # Check if lesson is within requested range
                if lesson_datetime >= start_date and lesson_datetime < end_date:
                    # Create event
                    summary = str(lesson.subject) if lesson.subject else "Unbekannt"

                    description_parts = []
                    if lesson.teacher and str(lesson.teacher):
                        teacher_str = str(lesson.teacher)
                        if teacher_str and teacher_str != "None":
                            description_parts.append(f"Lehrer: {teacher_str}")
                    if lesson.room and str(lesson.room):
                        room_str = str(lesson.room)
                        if room_str and room_str != "None":
                            description_parts.append(f"Raum: {room_str}")
                    if lesson.information and str(lesson.information):
                        info_str = str(lesson.information)
                        if info_str and info_str != "None":
                            description_parts.append(f"Info: {info_str}")

                    description = "\n".join(description_parts) if description_parts else None

                    event = CalendarEvent(
                        start=lesson_datetime,
                        end=lesson_end_datetime,
                        summary=summary,
                        description=description,
                    )

                    events.append(event)

                week_start += timedelta(days=7)

        return sorted(events, key=lambda e: e.start)
