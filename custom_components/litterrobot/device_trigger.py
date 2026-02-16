"""Device triggers for Litter-Robot."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .hub import EVENT_LITTERROBOT

TRIGGER_TYPES = {
    "clean_cycle_complete",
    "waste_drawer_full",
    "robot_online",
    "robot_offline",
    "pet_visit",
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return a list of triggers for a device."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        return []

    # Determine if this is a pet device or a robot device
    identifiers = device.identifiers
    is_pet = False
    serial = None
    for domain, identifier in identifiers:
        if domain == DOMAIN:
            serial = identifier
            # Pet devices have model "Pet"
            if device.model == "Pet":
                is_pet = True
            break

    if serial is None:
        return []

    triggers = []
    if is_pet:
        trigger_types = {"pet_visit"}
    else:
        trigger_types = {
            "clean_cycle_complete",
            "waste_drawer_full",
            "robot_online",
            "robot_offline",
        }

    for trigger_type in trigger_types:
        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: trigger_type,
            }
        )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(config[CONF_DEVICE_ID])
    if device is None:
        raise ValueError(f"Device {config[CONF_DEVICE_ID]} not found")

    # Get the serial/pet_id from device identifiers
    device_identifier = None
    for domain, identifier in device.identifiers:
        if domain == DOMAIN:
            device_identifier = identifier
            break

    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: EVENT_LITTERROBOT,
            event_trigger.CONF_EVENT_DATA: {
                "type": config[CONF_TYPE],
                "device_id": device_identifier,
            },
        }
    )

    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )
