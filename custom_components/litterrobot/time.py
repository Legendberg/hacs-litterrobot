"""Support for Litter-Robot sleep schedule time entities."""
from __future__ import annotations

from copy import deepcopy
from datetime import time
from typing import Any, Callable

from pylitterbot.robot import Robot

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LitterRobotControlEntity, is_litter_robot, is_lr5
from .hub import LitterRobotHub

WEEKDAY_DAYS = [0, 1, 2, 3, 4]
WEEKEND_DAYS = [5, 6]


def _minutes_to_time(minutes: int) -> time | None:
    """Convert minutes from midnight to a time object."""
    if minutes is None:
        return None
    hours, mins = divmod(int(minutes), 60)
    return time(hour=hours % 24, minute=mins)


def _time_to_minutes(t: time) -> int:
    """Convert a time object to minutes from midnight."""
    return t.hour * 60 + t.minute


def _get_schedule_time(robot: Robot, days: list[int], field: str) -> time | None:
    """Get the time value from the first matching day in the schedule."""
    schedules = robot._data.get("sleepSchedules", [])
    for schedule in schedules:
        if schedule.get("dayOfWeek") in days:
            return _minutes_to_time(schedule.get(field, 0))
    return None


async def _patch_schedule_time(
    robot: Robot, days: list[int], field: str, value: time
) -> None:
    """Patch the schedule time for the given days."""
    schedules = deepcopy(robot._data.get("sleepSchedules", []))
    if not schedules:
        schedules = [
            {"dayOfWeek": d, "isEnabled": False, "sleepTime": 0, "wakeTime": 0}
            for d in range(7)
        ]
    minutes = _time_to_minutes(value)
    for schedule in schedules:
        if schedule.get("dayOfWeek") in days:
            schedule[field] = minutes
    await robot._patch(
        f"robots/{robot.serial}", json={"sleepSchedules": schedules}
    )
    robot._update_data({"sleepSchedules": schedules}, partial=True)


class LitterRobotSleepTimeEntity(LitterRobotControlEntity, TimeEntity):
    """Litter-Robot sleep schedule time entity."""

    def __init__(
        self,
        robot: Robot,
        entity_type: str,
        hub: LitterRobotHub,
        days: list[int],
        field: str,
    ) -> None:
        """Init a sleep time entity."""
        super().__init__(robot=robot, entity_type=entity_type, hub=hub)
        self._days = days
        self._field = field

    @property
    def native_value(self) -> time | None:
        """Return the current time value."""
        return _get_schedule_time(self.robot, self._days, self._field)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._field == "sleepTime":
            return "mdi:weather-night"
        return "mdi:weather-sunny"

    async def async_set_value(self, value: time) -> None:
        """Set the time value."""
        await self.perform_action_and_refresh(
            _patch_schedule_time, self.robot, self._days, self._field, value
        )


ROBOT_TIMES: list[
    tuple[str, list[int], str, Callable[[Robot], bool] | None]
] = [
    ("Sleep Start Weekday", WEEKDAY_DAYS, "sleepTime", is_lr5),
    ("Sleep End Weekday", WEEKDAY_DAYS, "wakeTime", is_lr5),
    ("Sleep Start Weekend", WEEKEND_DAYS, "sleepTime", is_lr5),
    ("Sleep End Weekend", WEEKEND_DAYS, "wakeTime", is_lr5),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot sleep time entities using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if not is_litter_robot(robot):
            continue
        for entity_type, days, field, model_filter in ROBOT_TIMES:
            if model_filter is not None and not model_filter(robot):
                continue
            entities.append(
                LitterRobotSleepTimeEntity(
                    robot=robot,
                    entity_type=entity_type,
                    hub=hub,
                    days=days,
                    field=field,
                )
            )

    async_add_entities(entities, True)
