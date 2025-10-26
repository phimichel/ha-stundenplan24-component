"""Test calendar with real sample data."""
from datetime import datetime, timedelta
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

    # Mock the data with our parsed plan
    coordinator.data = {
        "timetable": plan,
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
        day_name = event.start.strftime("%A, %Y-%m-%d")
        if day_name not in events_by_day:
            events_by_day[day_name] = []
        events_by_day[day_name].append(event)

    print(f"\nEvents grouped by day:")
    for day_name in sorted(events_by_day.keys()):
        day_events = events_by_day[day_name]
        print(f"  {day_name}: {len(day_events)} event(s)")
        for event in day_events[:3]:  # First 3 events
            print(f"    - {event.start.strftime('%H:%M')}-{event.end.strftime('%H:%M')}: {event.summary}")

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
    assert len(monday_events) == 14, f"Expected 14 events on Monday, got {len(monday_events)}"
    assert len(tuesday_events) == 0, f"Expected 0 events on Tuesday, got {len(tuesday_events)}"

    # Verify events are sorted by time
    for i in range(len(monday_events) - 1):
        assert monday_events[i].start <= monday_events[i+1].start, \
            "Events should be sorted by start time"

    print("\n✓ All events correctly placed on the plan date (Monday)")
    print("✓ Events are sorted by time")
