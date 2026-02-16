"""Support for Litter-Robot select entities."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from pylitterbot.robot import Robot
from pylitterbot.robot.litterrobot5 import BrightnessLevel, NightLightMode

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import (
    LitterRobotControlEntity,
    LitterRobotEntityDescription,
    is_litter_robot,
    is_feeder_robot,
    is_lr5,
)
from .hub import LitterRobotHub

_BRIGHTNESS_LABEL_TO_LEVEL = {
    "Low": BrightnessLevel.LOW,
    "Medium": BrightnessLevel.MEDIUM,
    "High": BrightnessLevel.HIGH,
}
_BRIGHTNESS_LEVEL_TO_LABEL = {v: k for k, v in _BRIGHTNESS_LABEL_TO_LEVEL.items()}

_MEAL_LABEL_TO_SIZE = {"1/8 cup": 0.125, "1/4 cup": 0.25}
_MEAL_SIZE_TO_LABEL = {v: k for k, v in _MEAL_LABEL_TO_SIZE.items()}


@dataclass(frozen=True, kw_only=True)
class LitterRobotSelectDescription(
    SelectEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot select entity."""

    current_fn: Callable[[Robot], str | None]
    select_fn: Callable[[Robot, str], Coroutine[Any, Any, Any]]
    icon_fn: Callable[[str | None], str] | None = None


def _night_light_icon(mode_str: str | None) -> str:
    """Return icon for night light mode."""
    if mode_str == NightLightMode.ON.value:
        return "mdi:lightbulb-on"
    if mode_str == NightLightMode.AUTO.value:
        return "mdi:lightbulb-auto"
    return "mdi:lightbulb-off"


ROBOT_SELECT_DESCRIPTIONS: tuple[LitterRobotSelectDescription, ...] = (
    LitterRobotSelectDescription(
        key="night_light_mode",
        entity_type="Night Light Mode",
        model_filter=is_lr5,
        options=[mode.value for mode in NightLightMode],
        current_fn=lambda r: r.night_light_mode.value if r.night_light_mode else None,
        select_fn=lambda r, o: r.set_night_light_mode(NightLightMode(o)),
        icon_fn=_night_light_icon,
    ),
    LitterRobotSelectDescription(
        key="panel_brightness",
        entity_type="Panel Brightness",
        icon="mdi:brightness-6",
        model_filter=is_lr5,
        options=["Low", "Medium", "High"],
        current_fn=lambda r: _BRIGHTNESS_LEVEL_TO_LABEL.get(r.panel_brightness),
        select_fn=lambda r, o: r.set_panel_brightness(_BRIGHTNESS_LABEL_TO_LEVEL[o]),
    ),
    LitterRobotSelectDescription(
        key="wait_time",
        entity_type="Wait Time",
        icon="mdi:timer-outline",
        model_filter=is_lr5,
        options=["3", "7", "15", "25", "30"],
        current_fn=lambda r: str(r.clean_cycle_wait_time_minutes),
        select_fn=lambda r, o: r.set_wait_time(int(o)),
    ),
)

FEEDER_SELECT_DESCRIPTIONS: tuple[LitterRobotSelectDescription, ...] = (
    LitterRobotSelectDescription(
        key="meal_insert_size",
        entity_type="Meal Insert Size",
        icon="mdi:bowl-mix-outline",
        options=["1/8 cup", "1/4 cup"],
        current_fn=lambda r: _MEAL_SIZE_TO_LABEL.get(r.meal_insert_size),
        select_fn=lambda r, o: r.set_meal_insert_size(_MEAL_LABEL_TO_SIZE[o]),
    ),
)


class LitterRobotSelect(LitterRobotControlEntity, SelectEntity):
    """Litter-Robot select entity driven by an entity description."""

    entity_description: LitterRobotSelectDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotSelectDescription,
    ) -> None:
        """Initialize a Litter-Robot select entity."""
        super().__init__(robot, description.entity_type, hub)
        self.entity_description = description
        self._attr_options = list(description.options)

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self.entity_description.current_fn(self.robot)

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        if self.entity_description.icon_fn:
            return self.entity_description.icon_fn(self.current_option)
        return self.entity_description.icon

    async def async_select_option(self, option: str) -> None:
        """Handle option selection."""
        await self.perform_action_and_refresh(
            self.entity_description.select_fn, self.robot, option
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot select entities using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if is_litter_robot(robot):
            for desc in ROBOT_SELECT_DESCRIPTIONS:
                if desc.model_filter and not desc.model_filter(robot):
                    continue
                entities.append(LitterRobotSelect(robot, hub, desc))
        elif is_feeder_robot(robot):
            for desc in FEEDER_SELECT_DESCRIPTIONS:
                entities.append(LitterRobotSelect(robot, hub, desc))

    async_add_entities(entities, True)
