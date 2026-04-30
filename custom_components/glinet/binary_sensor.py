"""Binary sensors for GL-iNet component."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .router import GLinetRouter

_LOGGER = logging.getLogger(__name__)


class WiFiRadioBinarySensorDescription(
    BinarySensorEntityDescription, frozen_or_thawed=True
):
    """Describes a WiFi radio binary sensor entity."""


# WiFi Radio Binary Sensor Descriptions
WIFI_RADIO_BINARY_SENSORS: list[WiFiRadioBinarySensorDescription] = [
    WiFiRadioBinarySensorDescription(
        key="up",
        name="Up",
        has_entity_name=True,
        icon="mdi:wifi-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    _LOGGER.debug("Setting up GL-iNet Binary Sensors")

    router: GLinetRouter = entry.runtime_data
    binary_sensors: list[WiFiRadioBinarySensor] = []

    # Add WiFi radio status binary sensors for each discovered radio
    for radio_name in router.wifi_radios:
        for description in WIFI_RADIO_BINARY_SENSORS:
            binary_sensors.append(
                WiFiRadioBinarySensor(
                    router=router,
                    radio_name=radio_name,
                    entity_description=description,
                )
            )

    if binary_sensors:
        async_add_entities(binary_sensors, True)


class WiFiRadioBinarySensor(BinarySensorEntity):
    """WiFi radio status binary sensor entity."""

    def __init__(
        self,
        router: GLinetRouter,
        radio_name: str,
        entity_description: WiFiRadioBinarySensorDescription,
    ) -> None:
        """Initialize the WiFi radio binary sensor."""
        self.router = router
        self._radio_name = radio_name
        self.entity_description: WiFiRadioBinarySensorDescription = entity_description
        self._attr_device_info = router.device_info
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        """Return the unique id of the binary sensor."""
        return f"glinet_binary_sensor/{self.router.factory_mac}/wifi_{self._radio_name}_{self.entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return True if the WiFi radio is up."""
        radio = self.router.wifi_radios.get(self._radio_name)
        if radio is None:
            return False
        return bool(radio.up)
