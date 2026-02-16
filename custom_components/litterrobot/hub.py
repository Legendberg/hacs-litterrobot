"""A wrapper 'hub' for the Litter-Robot API."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from pylitterbot import Account
from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL_SECONDS = 10

EVENT_LITTERROBOT = "litterrobot_event"


class LitterRobotHub:
    """A Litter-Robot hub wrapper class."""

    def __init__(self, hass: HomeAssistant, data: dict) -> None:
        """Initialize the Litter-Robot hub."""
        self.hass = hass
        self._data = data
        self.account = None
        self.logged_in = False
        self._previous_states: dict[str, dict[str, Any]] = {}

        async def _async_update_data() -> bool:
            """Update all device states from the Litter-Robot API."""
            await self.account.refresh_robots()
            for pet in self.account.pets:
                try:
                    await pet.refresh()
                    await pet.fetch_weight_history(limit=500)
                except Exception:
                    pass
            self._check_and_fire_events()
            return True

        self.coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=_async_update_data,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    def _get_robot_state(self, robot) -> dict[str, Any]:
        """Get a snapshot of relevant robot state for event diffing."""
        state: dict[str, Any] = {
            "status": getattr(robot, "status", None),
            "is_online": getattr(robot, "is_online", None),
        }
        waste_level = getattr(robot, "waste_drawer_level", None)
        if waste_level is not None:
            state["waste_drawer_level"] = waste_level
        return state

    def _get_pet_state(self, pet) -> dict[str, Any]:
        """Get a snapshot of relevant pet state for event diffing."""
        history = getattr(pet, "weight_history", [])
        return {
            "weight_history_count": len(history),
        }

    def _check_and_fire_events(self) -> None:
        """Compare current states to previous and fire events for significant changes."""
        from pylitterbot.enums import LitterBoxStatus

        # Check robot state changes
        for robot in self.account.robots:
            key = f"robot_{robot.serial}"
            current = self._get_robot_state(robot)
            previous = self._previous_states.get(key)

            if previous is not None:
                base_data = {
                    "device_id": robot.serial,
                    "robot_name": robot.name,
                    "serial": robot.serial,
                }

                # Clean cycle complete
                prev_status = previous.get("status")
                curr_status = current.get("status")
                if (
                    prev_status == LitterBoxStatus.CLEAN_CYCLE
                    and curr_status == LitterBoxStatus.READY
                ):
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "clean_cycle_complete", **base_data},
                    )

                # Waste drawer full
                prev_waste = previous.get("waste_drawer_level")
                curr_waste = current.get("waste_drawer_level")
                if (
                    curr_waste is not None
                    and curr_waste >= 100
                    and (prev_waste is None or prev_waste < 100)
                ):
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "waste_drawer_full", "level": curr_waste, **base_data},
                    )

                # Robot online/offline
                prev_online = previous.get("is_online")
                curr_online = current.get("is_online")
                if prev_online is False and curr_online is True:
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "robot_online", **base_data},
                    )
                elif prev_online is True and curr_online is False:
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "robot_offline", **base_data},
                    )

            self._previous_states[key] = current

        # Check pet state changes
        for pet in self.account.pets:
            key = f"pet_{pet.id}"
            current = self._get_pet_state(pet)
            previous = self._previous_states.get(key)

            if previous is not None:
                prev_count = previous.get("weight_history_count", 0)
                curr_count = current.get("weight_history_count", 0)
                if curr_count > prev_count:
                    # New weight history entry = pet visit
                    history = getattr(pet, "weight_history", [])
                    latest_weight = (
                        round(history[0].weight, 2) if history else None
                    )
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {
                            "type": "pet_visit",
                            "device_id": pet.id,
                            "pet_name": pet.name,
                            "pet_id": pet.id,
                            "weight": latest_weight,
                        },
                    )

            self._previous_states[key] = current

    async def login(self, load_robots: bool = False) -> None:
        """Login to Litter-Robot."""
        self.logged_in = False
        self.account = Account()
        try:
            await self.account.connect(
                username=self._data[CONF_USERNAME],
                password=self._data[CONF_PASSWORD],
                load_robots=load_robots,
            )
            try:
                await self.account.load_pets()
            except Exception as ex:
                _LOGGER.warning("Unable to load pets: %s", ex)
            self.logged_in = True
            return self.logged_in
        except LitterRobotLoginException as ex:
            _LOGGER.error("Invalid credentials")
            raise ex
        except LitterRobotException as ex:
            _LOGGER.error("Unable to connect to Litter-Robot API")
            raise ex
