"""Support for Litter-Robot number entities."""
from __future__ import annotations

from typing import Callable

from pylitterbot.robot import Robot

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LitterRobotControlEntity, is_litter_robot, is_lr5
from .hub import LitterRobotHub


class LitterRobotNightLightBrightnessNumber(LitterRobotControlEntity, NumberEntity):
    """Litter-Robot 5 Night Light Brightness number."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1

    @property
    def native_value(self) -> float:
        """Return the current night light brightness."""
        return float(self.robot.night_light_brightness)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:brightness-percent"

    async def async_set_native_value(self, value: float) -> None:
        """Set the night light brightness."""
        await self.perform_action_and_refresh(
            self.robot.set_night_light_brightness, int(value)
        )


ROBOT_NUMBERS: list[
    tuple[type[LitterRobotControlEntity], str, Callable[[Robot], bool] | None]
] = [
    (LitterRobotNightLightBrightnessNumber, "Night Light Brightness", is_lr5),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot number entities using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if not is_litter_robot(robot):
            continue
        for number_class, entity_type, model_filter in ROBOT_NUMBERS:
            if model_filter is not None and not model_filter(robot):
                continue
            entities.append(
                number_class(robot=robot, entity_type=entity_type, hub=hub)
            )

    async_add_entities(entities, True)
