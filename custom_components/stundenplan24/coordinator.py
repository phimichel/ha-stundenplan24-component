"""DataUpdateCoordinator for stundenplan24."""
from __future__ import annotations

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
        """Set up the coordinator."""
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
            today = datetime.now().date()
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

            # Fetch Indiware Mobil plan (timetable)
            if mobil_clients:
                try:
                    # Get available dates first
                    available_dates = await mobil_clients[0].fetch_dates()

                    if available_dates:
                        # Fetch the most recent plan
                        latest_file = list(available_dates.keys())[0]
                        plan_response = await mobil_clients[0].fetch_plan(
                            date_or_filename=latest_file
                        )

                        # Parse XML to IndiwareMobilPlan
                        from .stundenplan24_py.indiware_mobil import IndiwareMobilPlan
                        import xml.etree.ElementTree as ET

                        root = ET.fromstring(plan_response.content)
                        timetable = IndiwareMobilPlan.from_xml(root)

                        # Filter to selected form if configured
                        selected_form = self.entry.options.get(CONF_FORM)
                        if selected_form:
                            timetable.forms = [
                                form for form in timetable.forms
                                if form.short_name == selected_form
                            ]
                            _LOGGER.debug("Filtered timetable to form: %s", selected_form)

                        data["timetable"] = timetable
                        _LOGGER.debug("Fetched timetable: %s", timetable.date if timetable else None)
                    else:
                        _LOGGER.warning("No timetable files available")
                        data["timetable"] = None
                except Exception as err:
                    _LOGGER.warning("Could not fetch timetable: %s", err)
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
