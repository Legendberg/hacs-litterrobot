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

from .const import (
    CONF_NOTIFY_CRITICAL,
    CONF_NOTIFY_EVENTS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_WARNING,
    DEFAULT_CRITICAL_EVENTS,
    DEFAULT_NOTIFY_EVENTS,
    DEFAULT_WARNING_EVENTS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL_SECONDS = 10

EVENT_LITTERROBOT = "litterrobot_event"


class LitterRobotHub:
    """A Litter-Robot hub wrapper class."""

    def __init__(self, hass: HomeAssistant, data) -> None:
        """Initialize the Litter-Robot hub.

        Args:
            hass: The Home Assistant instance.
            data: Either a ConfigEntry (from async_setup_entry) or a plain dict
                  (from config flow validation).
        """
        self.hass = hass
        if hasattr(data, "data"):
            # ConfigEntry object
            self._entry = data
            self._data = data.data
        else:
            # Plain dict (used during config flow validation)
            self._entry = None
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
            "is_drawer_removed": getattr(robot, "is_drawer_removed", None),
            "is_bonnet_removed": getattr(robot, "is_bonnet_removed", None),
        }
        waste_level = getattr(robot, "waste_drawer_level", None)
        if waste_level is not None:
            state["waste_drawer_level"] = waste_level
        pinch = getattr(robot, "pinch_status", None)
        if pinch is not None:
            state["pinch_status"] = str(pinch)
        motor = getattr(robot, "globe_motor_fault_status", None)
        if motor is not None:
            state["motor_fault_status"] = str(motor)
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
                    self.hass.async_create_task(
                        self._send_notification(
                            "clean_cycle_complete",
                            "Litter-Robot: Clean Cycle Complete",
                            f"{robot.name} finished a clean cycle.",
                        )
                    )

                # Cat sensor interrupted (cat jumped in during cycle)
                if (
                    prev_status == LitterBoxStatus.CLEAN_CYCLE
                    and curr_status == LitterBoxStatus.CAT_SENSOR_INTERRUPTED
                ):
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "cat_sensor_interrupted", **base_data},
                    )
                    self.hass.async_create_task(
                        self._send_notification(
                            "cat_sensor_interrupted",
                            "Litter-Robot: Cat Interrupted Cycle",
                            f"{robot.name} cycle was interrupted by cat sensor. "
                            "The unit will retry after the wait time.",
                        )
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
                    self.hass.async_create_task(
                        self._send_notification(
                            "waste_drawer_full",
                            "Litter-Robot: Waste Drawer Full",
                            f"{robot.name} waste drawer is FULL ({curr_waste}%). "
                            "Please empty the waste drawer soon.",
                        )
                    )

                # Robot online/offline
                prev_online = previous.get("is_online")
                curr_online = current.get("is_online")
                if prev_online is False and curr_online is True:
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "robot_online", **base_data},
                    )
                    self.hass.async_create_task(
                        self._send_notification(
                            "robot_online",
                            "Litter-Robot: Robot Online",
                            f"{robot.name} is back ONLINE.",
                        )
                    )
                elif prev_online is True and curr_online is False:
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "robot_offline", **base_data},
                    )
                    self.hass.async_create_task(
                        self._send_notification(
                            "robot_offline",
                            "Litter-Robot: Robot Offline",
                            f"{robot.name} went OFFLINE. "
                            "Check power and WiFi connection.",
                        )
                    )

                # Drawer removed
                prev_drawer = previous.get("is_drawer_removed")
                curr_drawer = current.get("is_drawer_removed")
                if prev_drawer is False and curr_drawer is True:
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "drawer_removed", **base_data},
                    )
                    self.hass.async_create_task(
                        self._send_notification(
                            "drawer_removed",
                            "Litter-Robot: Drawer Removed",
                            f"{robot.name} waste drawer has been removed. "
                            "Replace the drawer to resume cycling.",
                        )
                    )

                # Bonnet removed
                prev_bonnet = previous.get("is_bonnet_removed")
                curr_bonnet = current.get("is_bonnet_removed")
                if prev_bonnet is False and curr_bonnet is True:
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "bonnet_removed", **base_data},
                    )
                    self.hass.async_create_task(
                        self._send_notification(
                            "bonnet_removed",
                            "Litter-Robot: Bonnet Removed",
                            f"{robot.name} bonnet has been removed. "
                            "Replace the bonnet to resume cycling.",
                        )
                    )

                # Pinch detected
                prev_pinch = previous.get("pinch_status")
                curr_pinch = current.get("pinch_status")
                if (
                    prev_pinch is not None
                    and prev_pinch == "NONE"
                    and curr_pinch is not None
                    and curr_pinch != "NONE"
                ):
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "pinch_detected", "status": curr_pinch, **base_data},
                    )
                    self.hass.async_create_task(
                        self._send_notification(
                            "pinch_detected",
                            "Litter-Robot: Pinch Detected",
                            f"{robot.name} detected a pinch condition. "
                            "Check for obstructions.",
                        )
                    )

                # Motor fault
                prev_motor = previous.get("motor_fault_status")
                curr_motor = current.get("motor_fault_status")
                if (
                    prev_motor is not None
                    and prev_motor == "NONE"
                    and curr_motor is not None
                    and curr_motor != "NONE"
                ):
                    self.hass.bus.async_fire(
                        EVENT_LITTERROBOT,
                        {"type": "motor_fault", "status": curr_motor, **base_data},
                    )
                    self.hass.async_create_task(
                        self._send_notification(
                            "motor_fault",
                            "Litter-Robot: Motor Fault",
                            f"{robot.name} has a motor fault. "
                            "The globe motor may need attention.",
                        )
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
                    self.hass.async_create_task(
                        self._send_notification(
                            "pet_visit",
                            "Litter-Robot: Pet Visit",
                            f"{pet.name} visited the litter box. "
                            f"Weight: {latest_weight} lbs",
                        )
                    )

            self._previous_states[key] = current

    async def _send_notification(self, event_type, title, message):
        """Send a push notification if configured."""
        if self._entry is None:
            return
        options = self._entry.options
        service_name = options.get(CONF_NOTIFY_SERVICE)
        if not service_name:
            return
        enabled = options.get(CONF_NOTIFY_EVENTS, DEFAULT_NOTIFY_EVENTS)
        if event_type not in enabled:
            return

        data = {"tag": f"litterrobot_{event_type}", "group": "litter-robot"}
        critical = options.get(CONF_NOTIFY_CRITICAL, DEFAULT_CRITICAL_EVENTS)
        warning = options.get(CONF_NOTIFY_WARNING, DEFAULT_WARNING_EVENTS)
        if event_type in critical:
            data["push"] = {"sound": {"name": "default", "critical": 1, "volume": 1.0}}
        elif event_type in warning:
            data["push"] = {"sound": "default", "interruption-level": "time-sensitive"}

        try:
            await self.hass.services.async_call(
                "notify",
                service_name,
                {"title": title, "message": message, "data": data},
            )
        except Exception:
            _LOGGER.warning("Failed to send notification via notify.%s", service_name)

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
