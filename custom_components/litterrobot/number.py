"""Support for Litter-Robot number entities."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from pylitterbot.robot import Robot

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import (
    LitterRobotControlEntity,
    LitterRobotEntityDescription,
    is_litter_robot,
    is_lr5,
)
from .hub import LitterRobotHub


@dataclass(frozen=True, kw_only=True)
class LitterRobotNumberDescription(
    NumberEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot number entity."""

    value_fn: Callable[[Robot], float]
    set_fn: Callable[[Robot, int], Coroutine[Any, Any, Any]]
    min_value: float = 0
    max_value: float = 100
    step: float = 1


NUMBER_DESCRIPTIONS: tuple[LitterRobotNumberDescription, ...] = (
    LitterRobotNumberDescription(
        key="night_light_brightness",
        entity_type="Night Light Brightness",
        icon="mdi:brightness-percent",
        model_filter=is_lr5,
        value_fn=lambda r: float(r.night_light_brightness),
        set_fn=lambda r, v: r.set_night_light_brightness(v),
        min_value=0,
        max_value=100,
        step=1,
    ),
)


class LitterRobotNumber(LitterRobotControlEntity, NumberEntity):
    """Litter-Robot number entity driven by an entity description."""

    entity_description: LitterRobotNumberDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotNumberDescription,
    ) -> None:
        """Initialize a Litter-Robot number entity."""
        super().__init__(robot, description.entity_type, hub)
        self.entity_description = description
        self._attr_native_min_value = description.min_value
        self._attr_native_max_value = description.max_value
        self._attr_native_step = description.step

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.entity_description.value_fn(self.robot)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self.perform_action_and_refresh(
            self.entity_description.set_fn, self.robot, int(value)
        )


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
        for desc in NUMBER_DESCRIPTIONS:
            if desc.model_filter and not desc.model_filter(robot):
                continue
            entities.append(LitterRobotNumber(robot, hub, desc))

    async_add_entities(entities, True)
