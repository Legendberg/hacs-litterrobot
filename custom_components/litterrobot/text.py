"""Support for Litter-Robot text entities."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from pylitterbot.robot import Robot

from homeassistant.components.text import TextEntity, TextEntityDescription
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
class LitterRobotTextDescription(
    TextEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot text entity."""

    value_fn: Callable[[Robot], str | None]
    set_fn: Callable[[Robot, str], Coroutine[Any, Any, Any]]
    min_length: int = 4
    max_length: int = 7
    pattern: str | None = None


TEXT_DESCRIPTIONS: tuple[LitterRobotTextDescription, ...] = (
    LitterRobotTextDescription(
        key="night_light_color",
        entity_type="Night Light Color",
        icon="mdi:palette",
        model_filter=is_lr5,
        value_fn=lambda r: r.night_light_color,
        set_fn=lambda r, v: r.set_night_light_color(v),
        min_length=4,
        max_length=7,
        pattern=r"#[0-9A-Fa-f]{3,6}",
    ),
)


class LitterRobotText(LitterRobotControlEntity, TextEntity):
    """Litter-Robot text entity driven by an entity description."""

    entity_description: LitterRobotTextDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotTextDescription,
    ) -> None:
        """Initialize a Litter-Robot text entity."""
        super().__init__(robot, description.entity_type, hub)
        self.entity_description = description
        self._attr_native_min = description.min_length
        self._attr_native_max = description.max_length
        if description.pattern:
            self._attr_pattern = description.pattern

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        return self.entity_description.value_fn(self.robot)

    async def async_set_value(self, value: str) -> None:
        """Set the value."""
        await self.perform_action_and_refresh(
            self.entity_description.set_fn, self.robot, value
        )


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
        for desc in TEXT_DESCRIPTIONS:
            if desc.model_filter and not desc.model_filter(robot):
                continue
            entities.append(LitterRobotText(robot, hub, desc))

    async_add_entities(entities, True)
