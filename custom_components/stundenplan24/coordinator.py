"""DataUpdateCoordinator for stundenplan24."""
from __future__ import annotations

from asyncio import Lock
from datetime import datetime, timedelta
import logging
from typing import Any

from .stundenplan24_py.client import IndiwareStundenplanerClient, Hosting

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_FORM,
    CONF_PASSWORD,
    CONF_SCHOOL_URL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class Stundenplan24Coordinator(DataUpdateCoordinator):
    """Class to manage fetching stundenplan24 data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.client: IndiwareStundenplanerClient | None = None
        self._setup_lock = Lock()

        # Store config data
        self.school_url = entry.data[CONF_SCHOOL_URL]
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_setup(self) -> None:
        """Set up the coordinator with double-check locking."""
        async with self._setup_lock:
            # Double-check pattern to prevent multiple initializations
            if self.client is not None:
                return

            # Create hosting object using deserialize method
            hosting = Hosting.deserialize({
                "creds": {
                    "username": self.username,
                    "password": self.password,
                },
                "endpoints": self.school_url,
            })

            # Initialize client
            self.client = IndiwareStundenplanerClient(hosting=hosting)

            _LOGGER.debug("Stundenplan24 client initialized for %s", self.school_url)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        if self.client is None:
            await self._async_setup()

        try:
            data = {}

            # Convert filter objects to lists
            mobil_clients = list(self.client.indiware_mobil_clients)
            substitution_clients = list(self.client.substitution_plan_clients)

            # Fetch substitution plan for today
            today = dt_util.now().date()
            tomorrow = today + timedelta(days=1)

            _LOGGER.debug("Fetching substitution plans for %s and %s", today, tomorrow)

            # Fetch today's substitution plan (student view)
            if substitution_clients:
                try:
                    today_plan = await substitution_clients[0].fetch_plan(
                        date_or_filename=today
                    )
                    data["substitution_today"] = today_plan
                    _LOGGER.debug("Fetched substitution plan for today: %s", today_plan.date if today_plan else None)
                except Exception as err:
                    _LOGGER.warning("Could not fetch substitution plan for today: %s", err)
                    data["substitution_today"] = None

                # Fetch tomorrow's substitution plan
                try:
                    tomorrow_plan = await substitution_clients[0].fetch_plan(
                        date_or_filename=tomorrow
                    )
                    data["substitution_tomorrow"] = tomorrow_plan
                    _LOGGER.debug("Fetched substitution plan for tomorrow: %s", tomorrow_plan.date if tomorrow_plan else None)
                except Exception as err:
                    _LOGGER.warning("Could not fetch substitution plan for tomorrow: %s", err)
                    data["substitution_tomorrow"] = None

            # Fetch Indiware Mobil plans (timetable)
            # Each plan contains ALL forms/classes for a specific day
            # We fetch multiple days to provide better calendar coverage
            if mobil_clients:
                try:
                    # Get available dates first
                    available_dates = await mobil_clients[0].fetch_dates()

                    if available_dates:
                        from .stundenplan24_py.indiware_mobil import IndiwareMobilPlan
                        import xml.etree.ElementTree as ET

                        # Fetch plans for up to 7 days (for weekly calendar view)
                        # Each plan file contains all forms, so we only fetch once per day
                        plans_by_date = {}
                        fetch_errors = {}
                        selected_form = self.entry.data.get(CONF_FORM)

                        # Get up to 7 most recent plan files
                        files_to_fetch = list(available_dates.keys())[:7]

                        for filename in files_to_fetch:
                            try:
                                plan_response = await mobil_clients[0].fetch_plan(
                                    date_or_filename=filename
                                )

                                # Validate XML content before parsing
                                content = plan_response.content

                                # Debug logging to understand content type
                                _LOGGER.debug(
                                    "Content type for %s: %s, length: %s, first 50 chars: %s",
                                    filename,
                                    type(content).__name__,
                                    len(content) if content else 0,
                                    repr(content[:50]) if content else None
                                )

                                # Basic validation: check if content looks like XML
                                # XML can start with <?xml declaration or directly with a tag <
                                if isinstance(content, bytes):
                                    stripped = content.strip()
                                    if not stripped or not stripped.startswith(b'<'):
                                        raise ValueError(f"Response is not XML (bytes): {repr(content[:100])}")
                                else:
                                    stripped = content.strip()
                                    if not stripped or not stripped.startswith('<'):
                                        raise ValueError(f"Response is not XML (string): {repr(content[:100])}")

                                # Parse XML to IndiwareMobilPlan
                                root = ET.fromstring(content)
                                plan = IndiwareMobilPlan.from_xml(root)

                                # Filter to selected form if configured
                                # This reduces memory usage since we only keep relevant data
                                if selected_form:
                                    plan.forms = [
                                        form for form in plan.forms
                                        if form.short_name == selected_form
                                    ]

                                # Store plan by date for easy lookup
                                plans_by_date[plan.date] = plan

                                _LOGGER.debug(
                                    "Fetched plan for %s with %d form(s)",
                                    plan.date,
                                    len(plan.forms)
                                )
                            except ET.ParseError as err:
                                fetch_errors[filename] = f"XML parse error: {err}"
                                _LOGGER.error("Failed to parse XML for %s: %s", filename, err)
                                continue
                            except ValueError as err:
                                fetch_errors[filename] = str(err)
                                _LOGGER.error("Invalid content for %s: %s", filename, err)
                                continue
                            except Exception as err:
                                fetch_errors[filename] = str(err)
                                _LOGGER.warning(
                                    "Could not fetch plan %s: %s",
                                    filename,
                                    err
                                )
                                continue

                        if plans_by_date:
                            # Store all plans indexed by date
                            data["timetables"] = plans_by_date

                            # Store fetch errors for diagnostics
                            if fetch_errors:
                                data["timetable_fetch_errors"] = fetch_errors
                                _LOGGER.info(
                                    "Fetched %d of %d timetables successfully, %d errors",
                                    len(plans_by_date),
                                    len(files_to_fetch),
                                    len(fetch_errors)
                                )

                            # For backward compatibility, also store the most recent plan
                            # as "timetable" (for existing sensors that expect it)
                            most_recent_date = max(plans_by_date.keys())
                            data["timetable"] = plans_by_date[most_recent_date]

                            _LOGGER.debug(
                                "Fetched %d daily timetables (most recent: %s)",
                                len(plans_by_date),
                                most_recent_date
                            )
                        else:
                            _LOGGER.warning("No timetables could be fetched")
                            data["timetables"] = {}
                            data["timetable"] = None
                    else:
                        _LOGGER.warning("No timetable files available")
                        data["timetables"] = {}
                        data["timetable"] = None
                except Exception as err:
                    _LOGGER.warning("Could not fetch timetables: %s", err)
                    data["timetables"] = {}
                    data["timetable"] = None

            return data

        except Exception as err:
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.client:
            await self.client.close()
            _LOGGER.debug("Stundenplan24 client closed")
