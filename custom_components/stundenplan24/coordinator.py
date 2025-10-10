"""DataUpdateCoordinator for stundenplan24."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import aiohttp
from stundenplan24_py.client import IndiwareStundenplanerClient
from stundenplan24_py.endpoints import Hosting, Credentials

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
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
        # Create aiohttp session
        session = async_get_clientsession(self.hass)

        # Create credentials
        credentials = Credentials(
            username=self.username,
            password=self.password,
        )

        # Create hosting object
        hosting = Hosting(
            url=self.school_url,
            credentials=credentials,
        )

        # Initialize client
        self.client = IndiwareStundenplanerClient(
            hosting=hosting,
            session=session,
        )

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

            # Fetch substitution plan for today
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)

            _LOGGER.debug("Fetching substitution plans for %s and %s", today, tomorrow)

            # Fetch today's substitution plan (student view)
            if self.client.substitution_plan_clients:
                try:
                    today_plan = await self.client.substitution_plan_clients[0].fetch_plan(
                        date_or_filename=today
                    )
                    data["substitution_today"] = today_plan
                    _LOGGER.debug("Fetched substitution plan for today: %s", today_plan.date if today_plan else None)
                except Exception as err:
                    _LOGGER.warning("Could not fetch substitution plan for today: %s", err)
                    data["substitution_today"] = None

                # Fetch tomorrow's substitution plan
                try:
                    tomorrow_plan = await self.client.substitution_plan_clients[0].fetch_plan(
                        date_or_filename=tomorrow
                    )
                    data["substitution_tomorrow"] = tomorrow_plan
                    _LOGGER.debug("Fetched substitution plan for tomorrow: %s", tomorrow_plan.date if tomorrow_plan else None)
                except Exception as err:
                    _LOGGER.warning("Could not fetch substitution plan for tomorrow: %s", err)
                    data["substitution_tomorrow"] = None

            # Fetch Indiware Mobil plan (timetable)
            if self.client.indiware_mobil_clients:
                try:
                    # Get available dates first
                    available_dates = await self.client.indiware_mobil_clients[0].fetch_dates()

                    if available_dates:
                        # Fetch the most recent plan
                        latest_file = available_dates[0]["filename"]
                        timetable = await self.client.indiware_mobil_clients[0].fetch_plan(
                            date_or_filename=latest_file
                        )
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
