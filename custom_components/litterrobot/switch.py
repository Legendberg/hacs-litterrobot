"""Support for Litter-Robot switches."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from pylitterbot.robot import Robot

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LitterRobotControlEntity, is_litter_robot, is_feeder_robot, is_lr5
from .hub import LitterRobotHub

WEEKDAY_DAYS = [0, 1, 2, 3, 4]
WEEKEND_DAYS = [5, 6]


def is_not_lr5(robot: Robot) -> bool:
    """Return True if the robot is NOT a Litter-Robot 5."""
    return not is_lr5(robot)


class LitterRobotNightLightModeSwitch(LitterRobotControlEntity, SwitchEntity):
    """Litter-Robot Night Light Mode Switch."""

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.robot.night_light_mode_enabled

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:lightbulb-on" if self.is_on else "mdi:lightbulb-off"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.perform_action_and_refresh(self.robot.set_night_light, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.perform_action_and_refresh(self.robot.set_night_light, False)


class LitterRobotPanelLockoutSwitch(LitterRobotControlEntity, SwitchEntity):
    """Litter-Robot Panel Lockout Switch."""

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.robot.panel_lock_enabled

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:lock" if self.is_on else "mdi:lock-open"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.perform_action_and_refresh(self.robot.set_panel_lockout, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.perform_action_and_refresh(self.robot.set_panel_lockout, False)


class FeederRobotGravityModeSwitch(LitterRobotControlEntity, SwitchEntity):
    """Feeder-Robot Gravity Mode Switch."""

    @property
    def is_on(self) -> bool:
        """Return true if gravity mode is enabled."""
        return self.robot.gravity_mode_enabled

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:arrow-down-bold" if self.is_on else "mdi:arrow-down-bold-outline"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn gravity mode on."""
        await self.perform_action_and_refresh(self.robot.set_gravity_mode, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn gravity mode off."""
        await self.perform_action_and_refresh(self.robot.set_gravity_mode, False)


class LitterRobotSleepModeSwitch(LitterRobotControlEntity, SwitchEntity):
    """Litter-Robot 5 Sleep Mode Switch (weekday or weekend)."""

    def __init__(
        self, robot: Robot, entity_type: str, hub: LitterRobotHub, days: list[int]
    ) -> None:
        """Init a sleep mode switch."""
        super().__init__(robot=robot, entity_type=entity_type, hub=hub)
        self._days = days

    @property
    def is_on(self) -> bool:
        """Return true if sleep mode is enabled for these days."""
        schedules = self.robot._data.get("sleepSchedules", [])
        return all(
            schedule.get("isEnabled", False)
            for schedule in schedules
            if schedule.get("dayOfWeek") in self._days
        )

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:sleep" if self.is_on else "mdi:sleep-off"

    async def _set_sleep_enabled(self, value: bool) -> None:
        """Enable or disable sleep for the configured days."""
        schedules = deepcopy(self.robot._data.get("sleepSchedules", []))
        if not schedules:
            schedules = [
                {"dayOfWeek": d, "isEnabled": False, "sleepTime": 0, "wakeTime": 0}
                for d in range(7)
            ]
        for schedule in schedules:
            if schedule.get("dayOfWeek") in self._days:
                schedule["isEnabled"] = value
        await self.robot._patch(
            f"robots/{self.robot.serial}", json={"sleepSchedules": schedules}
        )
        self.robot._update_data({"sleepSchedules": schedules}, partial=True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn sleep mode on."""
        await self.perform_action_and_refresh(self._set_sleep_enabled, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn sleep mode off."""
        await self.perform_action_and_refresh(self._set_sleep_enabled, False)


ROBOT_SWITCHES: list[
    tuple[type[LitterRobotControlEntity], str, Callable[[Robot], bool] | None]
] = [
    (LitterRobotNightLightModeSwitch, "Night Light Mode", is_not_lr5),
    (LitterRobotPanelLockoutSwitch, "Panel Lockout", None),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot switches using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if is_litter_robot(robot):
            for switch_class, entity_type, model_filter in ROBOT_SWITCHES:
                if model_filter is not None and not model_filter(robot):
                    continue
                entities.append(
                    switch_class(robot=robot, entity_type=entity_type, hub=hub)
                )
            if is_lr5(robot):
                entities.append(
                    LitterRobotSleepModeSwitch(
                        robot=robot, entity_type="Sleep Mode Weekday", hub=hub, days=WEEKDAY_DAYS
                    )
                )
                entities.append(
                    LitterRobotSleepModeSwitch(
                        robot=robot, entity_type="Sleep Mode Weekend", hub=hub, days=WEEKEND_DAYS
                    )
                )
        elif is_feeder_robot(robot):
            entities.append(
                LitterRobotNightLightModeSwitch(robot=robot, entity_type="Night Light Mode", hub=hub)
            )
            entities.append(
                LitterRobotPanelLockoutSwitch(robot=robot, entity_type="Panel Lockout", hub=hub)
            )
            entities.append(
                FeederRobotGravityModeSwitch(robot=robot, entity_type="Gravity Mode", hub=hub)
            )

    async_add_entities(entities, True)
