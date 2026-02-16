"""Support for Litter-Robot switches."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from pylitterbot.robot import Robot

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
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

WEEKDAY_DAYS = [0, 1, 2, 3, 4]
WEEKEND_DAYS = [5, 6]


def is_not_lr5(robot: Robot) -> bool:
    """Return True if the robot is NOT a Litter-Robot 5."""
    return not is_lr5(robot)


@dataclass(frozen=True, kw_only=True)
class LitterRobotSwitchDescription(
    SwitchEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot switch."""

    is_on_fn: Callable[[Robot], bool]
    turn_on_fn: Callable[[Robot], Coroutine[Any, Any, Any]]
    turn_off_fn: Callable[[Robot], Coroutine[Any, Any, Any]]
    icon_fn: Callable[[bool], str] | None = None


ROBOT_SWITCH_DESCRIPTIONS: tuple[LitterRobotSwitchDescription, ...] = (
    LitterRobotSwitchDescription(
        key="night_light_mode",
        entity_type="Night Light Mode",
        model_filter=is_not_lr5,
        is_on_fn=lambda r: r.night_light_mode_enabled,
        turn_on_fn=lambda r: r.set_night_light(True),
        turn_off_fn=lambda r: r.set_night_light(False),
        icon_fn=lambda v: "mdi:lightbulb-on" if v else "mdi:lightbulb-off",
    ),
    LitterRobotSwitchDescription(
        key="panel_lockout",
        entity_type="Panel Lockout",
        is_on_fn=lambda r: r.panel_lock_enabled,
        turn_on_fn=lambda r: r.set_panel_lockout(True),
        turn_off_fn=lambda r: r.set_panel_lockout(False),
        icon_fn=lambda v: "mdi:lock" if v else "mdi:lock-open",
    ),
)

FEEDER_SWITCH_DESCRIPTIONS: tuple[LitterRobotSwitchDescription, ...] = (
    LitterRobotSwitchDescription(
        key="feeder_night_light",
        entity_type="Night Light Mode",
        is_on_fn=lambda r: r.night_light_mode_enabled,
        turn_on_fn=lambda r: r.set_night_light(True),
        turn_off_fn=lambda r: r.set_night_light(False),
        icon_fn=lambda v: "mdi:lightbulb-on" if v else "mdi:lightbulb-off",
    ),
    LitterRobotSwitchDescription(
        key="feeder_panel_lockout",
        entity_type="Panel Lockout",
        is_on_fn=lambda r: r.panel_lock_enabled,
        turn_on_fn=lambda r: r.set_panel_lockout(True),
        turn_off_fn=lambda r: r.set_panel_lockout(False),
        icon_fn=lambda v: "mdi:lock" if v else "mdi:lock-open",
    ),
    LitterRobotSwitchDescription(
        key="gravity_mode",
        entity_type="Gravity Mode",
        is_on_fn=lambda r: r.gravity_mode_enabled,
        turn_on_fn=lambda r: r.set_gravity_mode(True),
        turn_off_fn=lambda r: r.set_gravity_mode(False),
        icon_fn=lambda v: "mdi:arrow-down-bold" if v else "mdi:arrow-down-bold-outline",
    ),
)


class LitterRobotSwitch(LitterRobotControlEntity, SwitchEntity):
    """Litter-Robot switch driven by an entity description."""

    entity_description: LitterRobotSwitchDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotSwitchDescription,
    ) -> None:
        """Initialize a Litter-Robot switch."""
        super().__init__(robot, description.entity_type, hub)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.entity_description.is_on_fn(self.robot)

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        if self.entity_description.icon_fn:
            return self.entity_description.icon_fn(self.is_on)
        return self.entity_description.icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.perform_action_and_refresh(
            self.entity_description.turn_on_fn, self.robot
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.perform_action_and_refresh(
            self.entity_description.turn_off_fn, self.robot
        )


class LitterRobotSleepModeSwitch(LitterRobotControlEntity, SwitchEntity):
    """Litter-Robot 5 Sleep Mode Switch (weekday or weekend).

    Kept as a custom class due to complex schedule patching logic.
    """

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
            for desc in ROBOT_SWITCH_DESCRIPTIONS:
                if desc.model_filter and not desc.model_filter(robot):
                    continue
                entities.append(LitterRobotSwitch(robot, hub, desc))
            if is_lr5(robot):
                entities.append(
                    LitterRobotSleepModeSwitch(
                        robot=robot, entity_type="Sleep Mode Weekday",
                        hub=hub, days=WEEKDAY_DAYS,
                    )
                )
                entities.append(
                    LitterRobotSleepModeSwitch(
                        robot=robot, entity_type="Sleep Mode Weekend",
                        hub=hub, days=WEEKEND_DAYS,
                    )
                )
        elif is_feeder_robot(robot):
            for desc in FEEDER_SWITCH_DESCRIPTIONS:
                entities.append(LitterRobotSwitch(robot, hub, desc))

    async_add_entities(entities, True)
