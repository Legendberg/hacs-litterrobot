"""Support for Litter-Robot sleep schedule time entities."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import time
from typing import Any

from pylitterbot.robot import Robot

from homeassistant.components.time import TimeEntity, TimeEntityDescription
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

WEEKDAY_DAYS = [0, 1, 2, 3, 4]
WEEKEND_DAYS = [5, 6]


@dataclass(frozen=True, kw_only=True)
class LitterRobotTimeDescription(
    TimeEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot time entity."""

    days: list[int]
    schedule_field: str


TIME_DESCRIPTIONS: tuple[LitterRobotTimeDescription, ...] = (
    LitterRobotTimeDescription(
        key="sleep_start_weekday",
        entity_type="Sleep Start Weekday",
        icon="mdi:weather-night",
        model_filter=is_lr5,
        days=WEEKDAY_DAYS,
        schedule_field="sleepTime",
    ),
    LitterRobotTimeDescription(
        key="sleep_end_weekday",
        entity_type="Sleep End Weekday",
        icon="mdi:weather-sunny",
        model_filter=is_lr5,
        days=WEEKDAY_DAYS,
        schedule_field="wakeTime",
    ),
    LitterRobotTimeDescription(
        key="sleep_start_weekend",
        entity_type="Sleep Start Weekend",
        icon="mdi:weather-night",
        model_filter=is_lr5,
        days=WEEKEND_DAYS,
        schedule_field="sleepTime",
    ),
    LitterRobotTimeDescription(
        key="sleep_end_weekend",
        entity_type="Sleep End Weekend",
        icon="mdi:weather-sunny",
        model_filter=is_lr5,
        days=WEEKEND_DAYS,
        schedule_field="wakeTime",
    ),
)


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

    entity_description: LitterRobotTimeDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotTimeDescription,
    ) -> None:
        """Init a sleep time entity."""
        super().__init__(robot=robot, entity_type=description.entity_type, hub=hub)
        self.entity_description = description
        self._days = description.days
        self._field = description.schedule_field

    @property
    def native_value(self) -> time | None:
        """Return the current time value."""
        return _get_schedule_time(self.robot, self._days, self._field)

    async def async_set_value(self, value: time) -> None:
        """Set the time value."""
        await self.perform_action_and_refresh(
            _patch_schedule_time, self.robot, self._days, self._field, value
        )


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
        for desc in TIME_DESCRIPTIONS:
            if desc.model_filter and not desc.model_filter(robot):
                continue
            entities.append(LitterRobotSleepTimeEntity(robot, hub, desc))

    async_add_entities(entities, True)
