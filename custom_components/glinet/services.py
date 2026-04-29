"""Domain services for GL-iNet (repeater / uplink Wi‑Fi)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, selector, service

from gli4py.error_handling import APIClientError, NonZeroResponse

from .const import (
    ATTR_CONFIG_ENTRY,
    DATA_SERVICE_REFS,
    DOMAIN,
    SERVICE_REPEATER_CONNECT,
    SERVICE_REPEATER_DISCONNECT,
    SERVICE_REPEATER_GET_SAVED_AP_LIST,
    SERVICE_REPEATER_SCAN,
)

if TYPE_CHECKING:
    from .router import GLinetRouter

_LOGGER = logging.getLogger(__name__)

_CONFIG_ENTRY_SELECTOR = selector.ConfigEntrySelector({"integration": DOMAIN})

SCHEMA_REPEATER_CONNECT = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY): _CONFIG_ENTRY_SELECTOR,
        vol.Required("ssid"): cv.string,
        vol.Required("password"): cv.string,
        vol.Optional("remember", default=True): cv.boolean,
        vol.Optional("manual", default=False): cv.boolean,
        vol.Optional("protocol", default="dhcp"): cv.string,
        vol.Optional("bssid"): cv.string,
        vol.Optional("extra"): dict,
    }
)

SCHEMA_REPEATER_SCAN = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY): _CONFIG_ENTRY_SELECTOR,
        vol.Optional("band"): cv.string,
    }
)

SCHEMA_REPEATER_DISCONNECT = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY): _CONFIG_ENTRY_SELECTOR,
    }
)

SCHEMA_REPEATER_GET_SAVED = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY): _CONFIG_ENTRY_SELECTOR,
    }
)


def _router_from_call(hass: HomeAssistant, call: ServiceCall) -> GLinetRouter:
    entry = service.async_get_config_entry(
        hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY]
    )
    return entry.runtime_data


@callback
def _register_services(hass: HomeAssistant) -> None:
    async def repeater_connect(call: ServiceCall) -> None:
        router = _router_from_call(hass, call)
        bssid = call.data.get("bssid")
        extra = call.data.get("extra")
        try:
            await router.api.repeater_connect(
                call.data["ssid"],
                call.data["password"],
                protocol=call.data["protocol"],
                remember=call.data["remember"],
                manual=call.data["manual"],
                bssid=bssid,
                extra=extra,
            )
        except (APIClientError, NonZeroResponse, ValueError, TypeError) as err:
            _LOGGER.debug("repeater_connect failed", exc_info=True)
            raise HomeAssistantError(
                "Could not connect repeater; check router logs and RPC compatibility."
            ) from err

    async def repeater_scan(call: ServiceCall) -> ServiceResponse:
        router = _router_from_call(hass, call)
        params = {"band": call.data["band"]} if call.data.get("band") else None
        try:
            return await router.api.repeater_scan(params)
        except (APIClientError, NonZeroResponse, ValueError, TypeError) as err:
            _LOGGER.debug("repeater_scan failed", exc_info=True)
            raise HomeAssistantError(
                "Repeater scan failed; verify firmware exposes repeater.scan."
            ) from err

    async def repeater_disconnect(call: ServiceCall) -> None:
        router = _router_from_call(hass, call)
        try:
            await router.api.repeater_disconnect()
        except (APIClientError, NonZeroResponse, ValueError, TypeError) as err:
            _LOGGER.debug("repeater_disconnect failed", exc_info=True)
            raise HomeAssistantError("Repeater disconnect failed.") from err

    async def repeater_get_saved_ap_list(call: ServiceCall) -> ServiceResponse:
        router = _router_from_call(hass, call)
        try:
            return await router.api.repeater_get_saved_ap_list(redact_secrets=True)
        except (APIClientError, NonZeroResponse, ValueError, TypeError) as err:
            _LOGGER.debug("repeater_get_saved_ap_list failed", exc_info=True)
            raise HomeAssistantError(
                "Could not read saved uplink networks from the router."
            ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_REPEATER_CONNECT,
        repeater_connect,
        schema=SCHEMA_REPEATER_CONNECT,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPEATER_SCAN,
        repeater_scan,
        schema=SCHEMA_REPEATER_SCAN,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPEATER_DISCONNECT,
        repeater_disconnect,
        schema=SCHEMA_REPEATER_DISCONNECT,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPEATER_GET_SAVED_AP_LIST,
        repeater_get_saved_ap_list,
        schema=SCHEMA_REPEATER_GET_SAVED,
        supports_response=SupportsResponse.OPTIONAL,
    )


@callback
def _unregister_services(hass: HomeAssistant) -> None:
    for name in (
        SERVICE_REPEATER_CONNECT,
        SERVICE_REPEATER_SCAN,
        SERVICE_REPEATER_DISCONNECT,
        SERVICE_REPEATER_GET_SAVED_AP_LIST,
    ):
        hass.services.async_remove(DOMAIN, name)


async def async_ensure_services(hass: HomeAssistant) -> None:
    """Register domain services when the first config entry is loaded."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    ref = domain_data.get(DATA_SERVICE_REFS, 0) + 1
    domain_data[DATA_SERVICE_REFS] = ref
    if ref == 1:
        _register_services(hass)


async def async_release_services(hass: HomeAssistant) -> None:
    """Remove domain services after the last config entry is unloaded."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    ref = max(domain_data.get(DATA_SERVICE_REFS, 1) - 1, 0)
    domain_data[DATA_SERVICE_REFS] = ref
    if ref == 0:
        _unregister_services(hass)
