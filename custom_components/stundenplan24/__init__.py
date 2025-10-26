"""The Stundenplan24 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import Stundenplan24Coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Stundenplan24 component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stundenplan24 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize coordinator
    coordinator = Stundenplan24Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator - for backward compatibility with tests, store as coordinator directly
    # Calendar platform will add itself to the same entry_id dict
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register shutdown handler
    entry.async_on_unload(coordinator.async_shutdown)

    # Register update listener for options flow changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        # Handle both old (coordinator only) and new (dict) format
        if isinstance(entry_data, Stundenplan24Coordinator):
            coordinator = entry_data
        else:
            coordinator = entry_data["coordinator"]
        await coordinator.async_shutdown()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
