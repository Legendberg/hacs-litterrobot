"""Support for Litter-Robot text entities."""
from __future__ import annotations

from typing import Callable

from pylitterbot.robot import Robot

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LitterRobotControlEntity, is_litter_robot, is_lr5
from .hub import LitterRobotHub


class LitterRobotNightLightColorText(LitterRobotControlEntity, TextEntity):
    """Litter-Robot 5 Night Light Color text input."""

    _attr_native_min = 4
    _attr_native_max = 7
    _attr_pattern = r"#[0-9A-Fa-f]{3,6}"

    @property
    def native_value(self) -> str | None:
        """Return the current night light color."""
        return self.robot.night_light_color

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:palette"

    async def async_set_value(self, value: str) -> None:
        """Set the night light color."""
        await self.perform_action_and_refresh(self.robot.set_night_light_color, value)


ROBOT_TEXTS: list[
    tuple[type[LitterRobotControlEntity], str, Callable[[Robot], bool] | None]
] = [
    (LitterRobotNightLightColorText, "Night Light Color", is_lr5),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot text entities using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if not is_litter_robot(robot):
            continue
        for text_class, entity_type, model_filter in ROBOT_TEXTS:
            if model_filter is not None and not model_filter(robot):
                continue
            entities.append(
                text_class(robot=robot, entity_type=entity_type, hub=hub)
            )

    async_add_entities(entities, True)
