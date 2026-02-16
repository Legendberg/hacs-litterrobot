"""Support for Litter-Robot select entities."""
from __future__ import annotations

from typing import Any, Callable

from pylitterbot.robot import Robot
from pylitterbot.robot.litterrobot5 import BrightnessLevel, NightLightMode

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LitterRobotControlEntity, is_litter_robot, is_feeder_robot, is_lr5
from .hub import LitterRobotHub


class LitterRobotNightLightModeSelect(LitterRobotControlEntity, SelectEntity):
    """Litter-Robot 5 Night Light Mode select."""

    _attr_options = [mode.value for mode in NightLightMode]

    @property
    def current_option(self) -> str | None:
        """Return the current night light mode."""
        mode = self.robot.night_light_mode
        if mode is not None:
            return mode.value
        return None

    @property
    def icon(self) -> str:
        """Return the icon."""
        mode = self.robot.night_light_mode
        if mode == NightLightMode.ON:
            return "mdi:lightbulb-on"
        if mode == NightLightMode.AUTO:
            return "mdi:lightbulb-auto"
        return "mdi:lightbulb-off"

    async def async_select_option(self, option: str) -> None:
        """Change the night light mode."""
        mode = NightLightMode(option)
        await self.perform_action_and_refresh(self.robot.set_night_light_mode, mode)


class LitterRobotPanelBrightnessSelect(LitterRobotControlEntity, SelectEntity):
    """Litter-Robot 5 Panel Brightness select."""

    _attr_options = ["Low", "Medium", "High"]

    _label_to_level = {
        "Low": BrightnessLevel.LOW,
        "Medium": BrightnessLevel.MEDIUM,
        "High": BrightnessLevel.HIGH,
    }
    _level_to_label = {v: k for k, v in _label_to_level.items()}

    @property
    def current_option(self) -> str | None:
        """Return the current panel brightness."""
        level = self.robot.panel_brightness
        return self._level_to_label.get(level)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:brightness-6"

    async def async_select_option(self, option: str) -> None:
        """Change the panel brightness."""
        level = self._label_to_level[option]
        await self.perform_action_and_refresh(self.robot.set_panel_brightness, level)


class LitterRobotWaitTimeSelect(LitterRobotControlEntity, SelectEntity):
    """Litter-Robot 5 Wait Time select."""

    _attr_options = ["3", "7", "15", "25", "30"]

    @property
    def current_option(self) -> str | None:
        """Return the current wait time."""
        return str(self.robot.clean_cycle_wait_time_minutes)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:timer-outline"

    async def async_select_option(self, option: str) -> None:
        """Change the wait time."""
        await self.perform_action_and_refresh(self.robot.set_wait_time, int(option))


class FeederRobotMealInsertSizeSelect(LitterRobotControlEntity, SelectEntity):
    """Feeder-Robot Meal Insert Size select."""

    _attr_options = ["1/8 cup", "1/4 cup"]

    _label_to_size = {"1/8 cup": 0.125, "1/4 cup": 0.25}
    _size_to_label = {v: k for k, v in _label_to_size.items()}

    @property
    def current_option(self) -> str | None:
        """Return the current meal insert size."""
        size = self.robot.meal_insert_size
        return self._size_to_label.get(size)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:bowl-mix-outline"

    async def async_select_option(self, option: str) -> None:
        """Change the meal insert size."""
        size = self._label_to_size[option]
        await self.perform_action_and_refresh(self.robot.set_meal_insert_size, size)


ROBOT_SELECTS: list[
    tuple[type[LitterRobotControlEntity], str, Callable[[Robot], bool] | None]
] = [
    (LitterRobotNightLightModeSelect, "Night Light Mode", is_lr5),
    (LitterRobotPanelBrightnessSelect, "Panel Brightness", is_lr5),
    (LitterRobotWaitTimeSelect, "Wait Time", is_lr5),
]


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
            for select_class, entity_type, model_filter in ROBOT_SELECTS:
                if model_filter is not None and not model_filter(robot):
                    continue
                entities.append(
                    select_class(robot=robot, entity_type=entity_type, hub=hub)
                )
        elif is_feeder_robot(robot):
            entities.append(
                FeederRobotMealInsertSizeSelect(
                    robot=robot, entity_type="Meal Insert Size", hub=hub
                )
            )

    async_add_entities(entities, True)
