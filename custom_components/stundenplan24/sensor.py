"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    # TODO: Get coordinator from hass.data
    # coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # For now, create a placeholder sensor
    _LOGGER.info("Setting up Stundenplan24 sensors")

    # TODO: Create actual sensors when coordinator is implemented
    # sensors = [
    #     Stundenplan24CurrentLessonSensor(coordinator),
    #     Stundenplan24NextLessonSensor(coordinator),
    #     Stundenplan24SubstitutionsTodaySensor(coordinator),
    # ]
    # async_add_entities(sensors)


class Stundenplan24Sensor(SensorEntity):
    """Base class for Stundenplan24 sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Stundenplan24",
            "manufacturer": "Stundenplan24",
        }
