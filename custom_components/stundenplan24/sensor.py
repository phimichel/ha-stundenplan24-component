"""Platform for sensor integration."""
from __future__ import annotations

from datetime import datetime, date, time, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ROOM,
    ATTR_SCHEDULE,
    ATTR_SUBJECT,
    ATTR_SUBSTITUTIONS,
    ATTR_TEACHER,
    DOMAIN,
)
from .coordinator import Stundenplan24Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]

    # Handle both coordinator-only and dict storage
    if isinstance(entry_data, Stundenplan24Coordinator):
        coordinator = entry_data
    else:
        coordinator = entry_data["coordinator"]

    sensors = [
        Stundenplan24SubstitutionsTodaySensor(coordinator),
        Stundenplan24SubstitutionsTomorrowSensor(coordinator),
        Stundenplan24NextLessonSensor(coordinator),
        Stundenplan24AdditionalInfoSensor(coordinator),
    ]

    async_add_entities(sensors)


class Stundenplan24Sensor(CoordinatorEntity, SensorEntity):
    """Base class for Stundenplan24 sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Stundenplan24Coordinator, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Stundenplan24",
            "manufacturer": "Stundenplan24",
            "model": "Student Schedule",
            "sw_version": "1.0",
        }


class Stundenplan24SubstitutionsTodaySensor(Stundenplan24Sensor):
    """Sensor for today's substitutions."""

    def __init__(self, coordinator: Stundenplan24Coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "substitutions_today")
        self._attr_name = "Vertretungen Heute"
        self._attr_icon = "mdi:calendar-today"

    @property
    def native_value(self) -> int | None:
        """Return the number of substitutions."""
        if not self.coordinator.data:
            return None

        plan = self.coordinator.data.get("substitution_today")
        if not plan or not plan.actions:
            return 0

        return len(plan.actions)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        plan = self.coordinator.data.get("substitution_today")
        if not plan:
            return {}

        substitutions = []
        if plan.actions:
            for action in plan.actions:
                substitution = {
                    "form": action.form,
                    "period": action.period,
                }

                if action.subject:
                    substitution["subject"] = str(action.subject)
                if action.teacher:
                    substitution["teacher"] = str(action.teacher)
                if action.room:
                    substitution["room"] = str(action.room)
                if action.info:
                    substitution["info"] = action.info

                # Add original values if changed
                if action.original_subject:
                    substitution["original_subject"] = action.original_subject
                if action.original_teacher:
                    substitution["original_teacher"] = action.original_teacher
                if action.original_room:
                    substitution["original_room"] = action.original_room

                substitutions.append(substitution)

        attrs = {
            ATTR_SUBSTITUTIONS: substitutions,
            "date": str(plan.date) if plan.date else None,
            "last_update": str(plan.timestamp) if plan.timestamp else None,
        }

        if plan.absent_teachers:
            attrs["absent_teachers"] = plan.absent_teachers
        if plan.absent_forms:
            attrs["absent_forms"] = plan.absent_forms
        if plan.additional_info:
            attrs["additional_info"] = plan.additional_info

        return attrs


class Stundenplan24SubstitutionsTomorrowSensor(Stundenplan24Sensor):
    """Sensor for tomorrow's substitutions."""

    def __init__(self, coordinator: Stundenplan24Coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "substitutions_tomorrow")
        self._attr_name = "Vertretungen Morgen"
        self._attr_icon = "mdi:calendar-arrow-right"

    @property
    def native_value(self) -> int | None:
        """Return the number of substitutions."""
        if not self.coordinator.data:
            return None

        plan = self.coordinator.data.get("substitution_tomorrow")
        if not plan or not plan.actions:
            return 0

        return len(plan.actions)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        plan = self.coordinator.data.get("substitution_tomorrow")
        if not plan:
            return {}

        substitutions = []
        if plan.actions:
            for action in plan.actions:
                substitution = {
                    "form": action.form,
                    "period": action.period,
                }

                if action.subject:
                    substitution["subject"] = str(action.subject)
                if action.teacher:
                    substitution["teacher"] = str(action.teacher)
                if action.room:
                    substitution["room"] = str(action.room)
                if action.info:
                    substitution["info"] = action.info

                substitutions.append(substitution)

        attrs = {
            ATTR_SUBSTITUTIONS: substitutions,
            "date": str(plan.date) if plan.date else None,
            "last_update": str(plan.timestamp) if plan.timestamp else None,
        }

        if plan.absent_teachers:
            attrs["absent_teachers"] = plan.absent_teachers
        if plan.additional_info:
            attrs["additional_info"] = plan.additional_info

        return attrs


class Stundenplan24NextLessonSensor(Stundenplan24Sensor):
    """Sensor for the next lesson."""

    def __init__(self, coordinator: Stundenplan24Coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "next_lesson")
        self._attr_name = "Nächste Stunde"
        self._attr_icon = "mdi:clock-outline"

    def _find_next_lesson(self) -> dict[str, Any] | None:
        """Find the next lesson from the timetable."""
        if not self.coordinator.data:
            return None

        timetable = self.coordinator.data.get("timetable")
        if not timetable or not timetable.forms:
            return None

        now = datetime.now()
        current_time = now.time()

        # Get the first form (assuming single student view)
        # TODO: Add form selection via config
        form = timetable.forms[0] if timetable.forms else None
        if not form or not form.lessons:
            return None

        # Find next lesson
        next_lesson = None
        for lesson in form.lessons:
            if lesson.start and lesson.start > current_time:
                if next_lesson is None or lesson.start < next_lesson.start:
                    next_lesson = lesson

        return next_lesson

    @property
    def native_value(self) -> str | None:
        """Return the subject of the next lesson."""
        lesson = self._find_next_lesson()
        if not lesson:
            return "Keine weiteren Stunden"

        if lesson.subject:
            return str(lesson.subject)

        return "Unbekannt"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        lesson = self._find_next_lesson()
        if not lesson:
            return {}

        attrs = {
            "period": lesson.period,
        }

        if lesson.start:
            attrs["start_time"] = str(lesson.start)
        if lesson.end:
            attrs["end_time"] = str(lesson.end)
        if lesson.teacher:
            attrs[ATTR_TEACHER] = str(lesson.teacher)
        if lesson.room:
            attrs[ATTR_ROOM] = str(lesson.room)
        if lesson.course2:
            attrs["course"] = lesson.course2
        if lesson.information:
            attrs["info"] = lesson.information

        return attrs


class Stundenplan24AdditionalInfoSensor(Stundenplan24Sensor):
    """Sensor for additional info (ZusatzInfo) from timetables."""

    def __init__(self, coordinator: Stundenplan24Coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "additional_info")
        self._attr_name = "Zusatzinformationen"
        self._attr_icon = "mdi:information-outline"

    def _get_info_for_date(self, target_date: date) -> list[str] | None:
        """Get ZusatzInfo for a specific date."""
        if not self.coordinator.data:
            return None

        # Try new multi-day structure first
        timetables = self.coordinator.data.get("timetables", {})

        if timetables and target_date in timetables:
            plan = timetables[target_date]
            if plan.additional_info:
                # Filter out empty lines and None values
                return [line for line in plan.additional_info if line and line.strip()]

        # Fallback to single timetable for today
        timetable = self.coordinator.data.get("timetable")
        if timetable and timetable.date == target_date:
            if timetable.additional_info:
                return [line for line in timetable.additional_info if line and line.strip()]

        return None

    @property
    def native_value(self) -> str | None:
        """Return the status of additional info."""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        today_info = self._get_info_for_date(today)
        tomorrow_info = self._get_info_for_date(tomorrow)

        count = 0
        if today_info:
            count += 1
        if tomorrow_info:
            count += 1

        if count == 0:
            return "Keine Informationen"
        elif count == 1:
            return "1 Tag mit Informationen"
        else:
            return f"{count} Tage mit Informationen"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        attrs = {}

        # Today's info
        today_info = self._get_info_for_date(today)
        if today_info:
            attrs["today"] = "\n".join(today_info)
            attrs["today_lines"] = today_info
            attrs["today_date"] = str(today)
        else:
            attrs["today"] = None
            attrs["today_lines"] = []

        # Tomorrow's info
        tomorrow_info = self._get_info_for_date(tomorrow)
        if tomorrow_info:
            attrs["tomorrow"] = "\n".join(tomorrow_info)
            attrs["tomorrow_lines"] = tomorrow_info
            attrs["tomorrow_date"] = str(tomorrow)
        else:
            attrs["tomorrow"] = None
            attrs["tomorrow_lines"] = []

        return attrs
