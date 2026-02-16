"""Litter-Robot entities for common data and methods."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import time
import logging
from types import MethodType
from typing import Any

from pylitterbot import LitterRobot, Robot
from pylitterbot.exceptions import InvalidCommandException
from pylitterbot.robot.feederrobot import FeederRobot
from pylitterbot.robot.litterrobot5 import LitterRobot5

from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .hub import LitterRobotHub

_LOGGER = logging.getLogger(__name__)

REFRESH_WAIT_TIME_SECONDS = 8


def is_litter_robot(robot: Robot) -> bool:
    """Return True if the robot is a Litter-Robot (not a Feeder-Robot)."""
    return isinstance(robot, LitterRobot)


def is_feeder_robot(robot: Robot) -> bool:
    """Return True if the robot is a Feeder-Robot."""
    return isinstance(robot, FeederRobot)


def is_lr5(robot: Robot) -> bool:
    """Return True if the robot is a Litter-Robot 5."""
    return isinstance(robot, LitterRobot5)


def is_lr5_pro(robot: Robot) -> bool:
    """Return True if the robot is a Litter-Robot 5 Pro."""
    return isinstance(robot, LitterRobot5) and robot.is_pro


@dataclass(frozen=True, kw_only=True)
class LitterRobotEntityDescription:
    """Mixin for Litter-Robot entity descriptions."""

    entity_type: str
    robot_attr: str = ""
    model_filter: Callable[[Robot], bool] | None = None


class LitterRobotEntity(CoordinatorEntity):
    """Generic Litter-Robot entity representing common data and methods."""

    def __init__(self, robot: Robot, entity_type: str, hub: LitterRobotHub) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(hub.coordinator)
        self.robot = robot
        self.entity_type = entity_type
        self.hub = hub

    @property
    def name(self) -> str:
        """Return the name of this entity."""
        return f"{self.robot.name} {self.entity_type}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.robot.serial}-{self.entity_type}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information for a Litter-Robot."""
        return {
            "identifiers": {(DOMAIN, self.robot.serial)},
            "name": self.robot.name,
            "manufacturer": "Litter-Robot",
            "model": self.robot.model,
        }


class LitterRobotControlEntity(LitterRobotEntity):
    """A Litter-Robot entity that can control the unit."""

    def __init__(self, robot: Robot, entity_type: str, hub: LitterRobotHub) -> None:
        """Init a Litter-Robot control entity."""
        super().__init__(robot=robot, entity_type=entity_type, hub=hub)
        self._refresh_callback = None

    async def perform_action_and_refresh(
        self, action: MethodType, *args: Any, **kwargs: Any
    ) -> bool:
        """Perform an action and initiates a refresh of the robot data after a few seconds."""

        try:
            await action(*args, **kwargs)
        except InvalidCommandException as ex:  # pragma: no cover
            # this exception should only occur if the underlying API for commands changes
            _LOGGER.error(ex)
            return False

        self.async_cancel_refresh_callback()
        self._refresh_callback = async_call_later(
            self.hass, REFRESH_WAIT_TIME_SECONDS, self.async_call_later_callback
        )
        return True

    async def async_call_later_callback(self, *_) -> None:
        """Perform refresh request on callback."""
        self._refresh_callback = None
        await self.coordinator.async_request_refresh()

    async def async_will_remove_from_hass(self) -> None:
        """Cancel refresh callback when entity is being removed from hass."""
        self.async_cancel_refresh_callback()

    @callback
    def async_cancel_refresh_callback(self):
        """Clear the refresh callback if it has not already fired."""
        if self._refresh_callback is not None:
            self._refresh_callback()
            self._refresh_callback = None

    @staticmethod
    def parse_time_at_default_timezone(time_str: str) -> time | None:
        """Parse a time string and add default timezone."""
        parsed_time = dt_util.parse_time(time_str)

        if parsed_time is None:
            return None

        return (
            dt_util.start_of_local_day()
            .replace(
                hour=parsed_time.hour,
                minute=parsed_time.minute,
                second=parsed_time.second,
            )
            .timetz()
        )
