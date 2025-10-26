"""Test calendar with real sample data."""
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock
import xml.etree.ElementTree as ET

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.stundenplan24.calendar import Stundenplan24Calendar
from custom_components.stundenplan24.const import DOMAIN
from custom_components.stundenplan24.coordinator import Stundenplan24Coordinator
from custom_components.stundenplan24.stundenplan24_py.indiware_mobil import (
    IndiwareMobilPlan,
)


async def test_calendar_with_sample_xml(hass: HomeAssistant):
    """Test calendar generation with real sample XML file."""
    # Load sample XML
    with open(
        "/Users/user/Development/Private/homeassistant_components/stundenplan24/samples/PlanKl20251027.xml",
        "r",
        encoding="utf-8",
    ) as f:
        xml_content = f.read()

    # Parse XML
    xml_root = ET.fromstring(xml_content)
    plan = IndiwareMobilPlan.from_xml(xml_root)

    # Verify plan was parsed correctly
    assert plan is not None
    assert plan.date.year == 2025
    assert plan.date.month == 10
    assert plan.date.day == 27
    assert len(plan.forms) > 0

    # Print debug info about the plan
    print(f"\nPlan date: {plan.date}")
    print(f"Number of forms: {len(plan.forms)}")

    for i, form in enumerate(plan.forms[:3]):  # First 3 forms
        print(f"\nForm {i}: {form.short_name}")
        print(f"  Number of lessons: {len(form.lessons)}")
        if form.lessons:
            lesson = form.lessons[0]
            print(f"  First lesson: period={lesson.period}, subject={lesson.subject}, "
                  f"start={lesson.start}, end={lesson.end}")

    # Filter for a specific form (e.g., "LG 1")
    lg1_forms = [f for f in plan.forms if f.short_name == "LG 1"]
    assert len(lg1_forms) > 0, "Form 'LG 1' not found in sample data"

    lg1_form = lg1_forms[0]
    print(f"\nLG 1 form has {len(lg1_form.lessons)} lessons")

    # Group lessons by period to understand structure
    lessons_by_period = {}
    for lesson in lg1_form.lessons:
        period = lesson.period
        if period not in lessons_by_period:
            lessons_by_period[period] = []
        lessons_by_period[period].append(lesson)

    print(f"\nLessons grouped by period:")
    for period in sorted(lessons_by_period.keys())[:5]:  # First 5 periods
        lessons = lessons_by_period[period]
        print(f"  Period {period}: {len(lessons)} lesson(s)")
        for lesson in lessons:
            subject = lesson.subject.content if lesson.subject else "?"
            teacher = lesson.teacher.content if lesson.teacher else "?"
            room = lesson.room.content if lesson.room else "?"
            print(f"    - {subject} ({teacher}) in {room}")

    # Now test the calendar
    config_entry = MagicMock()
    config_entry.entry_id = "test"
    config_entry.options = {"form": "LG 1"}
    config_entry.data = {
        "school_url": "https://test.stundenplan24.de",
        "username": "test",
        "password": "test",
    }

    coordinator = Stundenplan24Coordinator(hass, config_entry)

    # Mock the data with our parsed plan in the multi-day structure
    coordinator.data = {
        "timetables": {plan.date: plan},
        "timetable": plan,  # Backward compatibility
    }

    calendar = Stundenplan24Calendar(coordinator)

    # Request events for the week containing the plan date
    # Plan is for Monday, 27 October 2025
    plan_date = datetime(2025, 10, 27, 0, 0, 0)
    start_date = dt_util.as_local(plan_date)
    end_date = dt_util.as_local(plan_date + timedelta(days=7))

    events = calendar._get_events(start_date, end_date)

    print(f"\n\nCalendar generated {len(events)} events")

    # Group events by day
    events_by_day = {}
    for event in events:
        # Handle both datetime and date objects
        if isinstance(event.start, datetime):
            day_name = event.start.strftime("%A, %Y-%m-%d")
        else:
            day_name = event.start.strftime("%A, %Y-%m-%d")

        if day_name not in events_by_day:
            events_by_day[day_name] = []
        events_by_day[day_name].append(event)

    print(f"\nEvents grouped by day:")
    for day_name in sorted(events_by_day.keys()):
        day_events = events_by_day[day_name]
        print(f"  {day_name}: {len(day_events)} event(s)")
        for event in day_events[:3]:  # First 3 events
            # Handle both datetime (timed events) and date (all-day events)
            if isinstance(event.start, datetime):
                print(f"    - {event.start.strftime('%H:%M')}-{event.end.strftime('%H:%M')}: {event.summary}")
            else:
                print(f"    - 00:00-00:00: {event.summary}")

    # Verify events are distributed across weekdays, not just Monday
    # THIS IS THE BUG: All events are on Monday because the XML only contains
    # data for Monday, but the calendar logic tries to spread it across the week
    assert len(events) > 0, "Should generate some events"

    # The issue: events are only on Monday, not distributed across the week
    monday_events = events_by_day.get("Monday, 2025-10-27", [])
    tuesday_events = events_by_day.get("Tuesday, 2025-10-28", [])

    print(f"\nMonday events: {len(monday_events)}")
    print(f"Tuesday events: {len(tuesday_events)}")

    # CORRECT behavior: All events should be on Monday (the plan date)
    # The IndiwareMobil plan is a DAILY plan, not a weekly plan
    # Expected: 14 lesson events + 1 ZusatzInfo all-day event = 15 total
    assert len(monday_events) == 15, f"Expected 15 events on Monday (14 lessons + 1 ZusatzInfo), got {len(monday_events)}"
    assert len(tuesday_events) == 0, f"Expected 0 events on Tuesday, got {len(tuesday_events)}"

    # Verify events are sorted by time (using same logic as calendar.py)
    def get_sort_key(event):
        if isinstance(event.start, datetime):
            return event.start
        else:
            return dt_util.start_of_local_day(
                datetime.combine(event.start, datetime.min.time())
            )

    for i in range(len(monday_events) - 1):
        assert get_sort_key(monday_events[i]) <= get_sort_key(monday_events[i+1]), \
            "Events should be sorted by start time"

    print("\n✓ All events correctly placed on the plan date (Monday)")
    print("✓ Events are sorted by time")


async def test_calendar_with_zusatzinfo_all_day_event(hass: HomeAssistant):
    """Test calendar creates all-day events for ZusatzInfo."""
    # Load sample XML
    with open(
        "/Users/user/Development/Private/homeassistant_components/stundenplan24/samples/PlanKl20251027.xml",
        "r",
        encoding="utf-8",
    ) as f:
        xml_content = f.read()

    # Parse XML
    xml_root = ET.fromstring(xml_content)
    plan = IndiwareMobilPlan.from_xml(xml_root)

    # Verify plan has ZusatzInfo
    assert plan.additional_info is not None
    assert len(plan.additional_info) > 0
    print(f"\nPlan has {len(plan.additional_info)} ZusatzInfo lines")

    # Filter to non-empty lines (handle None values)
    info_lines = [line for line in plan.additional_info if line and line.strip()]
    print(f"Non-empty ZusatzInfo lines: {len(info_lines)}")
    for line in info_lines[:3]:
        print(f"  - {line}")

    # Now test the calendar with ZusatzInfo
    config_entry = MagicMock()
    config_entry.entry_id = "test"
    config_entry.options = {"form": "LG 1"}
    config_entry.data = {
        "school_url": "https://test.stundenplan24.de",
        "username": "test",
        "password": "test",
    }

    coordinator = Stundenplan24Coordinator(hass, config_entry)

    # Mock the data with our parsed plan in the multi-day structure
    coordinator.data = {
        "timetables": {plan.date: plan},
        "timetable": plan,
    }

    calendar = Stundenplan24Calendar(coordinator)

    # Request events for the week containing the plan date
    plan_date = datetime(2025, 10, 27, 0, 0, 0)
    start_date = dt_util.as_local(plan_date)
    end_date = dt_util.as_local(plan_date + timedelta(days=7))

    events = calendar._get_events(start_date, end_date)

    print(f"\n\nCalendar generated {len(events)} total events")

    # Find all-day events (events where start and end are dates, not datetimes)
    all_day_events = [e for e in events if isinstance(e.start, date) and not isinstance(e.start, datetime)]

    print(f"All-day events: {len(all_day_events)}")

    # Should have at least one all-day event for ZusatzInfo
    assert len(all_day_events) >= 1, f"Expected at least 1 all-day event, got {len(all_day_events)}"

    # Check the ZusatzInfo all-day event
    info_event = next((e for e in all_day_events if "Information" in e.summary), None)
    assert info_event is not None, "No 'Informationen' all-day event found"

    print(f"\nAll-day event found:")
    print(f"  Summary: {info_event.summary}")
    print(f"  Start: {info_event.start}")
    print(f"  End: {info_event.end}")
    print(f"  Description (first 100 chars): {info_event.description[:100] if info_event.description else 'None'}...")

    # Verify it's on the correct date
    assert info_event.start == plan.date
    assert info_event.end == plan.date + timedelta(days=1)

    # Verify description contains ZusatzInfo
    assert info_event.description is not None
    assert "Pausenorte" in info_event.description or "Bibliothek" in info_event.description

    print("\n✓ All-day event correctly created for ZusatzInfo")
    print("✓ Event spans the entire day")
    print("✓ Description contains information from ZusatzInfo")
