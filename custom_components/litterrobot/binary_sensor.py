"""Support for Litter-Robot binary sensors."""
from __future__ import annotations

from typing import Callable

from pylitterbot.robot import Robot

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LitterRobotEntity, is_litter_robot, is_feeder_robot, is_lr5, is_lr5_pro
from .hub import LitterRobotHub


class LitterRobotBinarySensor(LitterRobotEntity, BinarySensorEntity):
    """Litter-Robot binary sensor."""

    def __init__(
        self,
        robot: Robot,
        entity_type: str,
        hub: LitterRobotHub,
        sensor_attribute: str,
    ) -> None:
        """Pass robot, entity_type and hub to LitterRobotEntity."""
        super().__init__(robot, entity_type, hub)
        self.sensor_attribute = sensor_attribute

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return getattr(self.robot, self.sensor_attribute, False)

    @property
    def device_class(self) -> str:
        """Return the device class."""
        return BinarySensorDeviceClass.PROBLEM


class LitterRobotDiagnosticBinarySensor(LitterRobotBinarySensor):
    """Litter-Robot diagnostic binary sensor (generic boolean)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_class(self) -> str:
        """Return the device class."""
        return None


class LitterRobotCameraAudioBinarySensor(LitterRobotBinarySensor):
    """Litter-Robot 5 Pro Camera Audio binary sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_class(self) -> str:
        """Return the device class."""
        return None

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:microphone" if self.is_on else "mdi:microphone-off"


ROBOT_BINARY_SENSORS: list[
    tuple[type[LitterRobotBinarySensor] | None, str, str, Callable[[Robot], bool] | None]
] = [
    (None, "Drawer Removed", "is_drawer_removed", is_lr5),
    (None, "Bonnet Removed", "is_bonnet_removed", is_lr5),
    (None, "Laser Dirty", "is_laser_dirty", is_lr5),
    (LitterRobotCameraAudioBinarySensor, "Camera Audio", "camera_audio_enabled", is_lr5_pro),
    (LitterRobotDiagnosticBinarySensor, "Online", "is_online", is_lr5),
    (LitterRobotDiagnosticBinarySensor, "Smart Weight", "is_smart_weight_enabled", is_lr5),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot binary sensors using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if is_litter_robot(robot):
            for sensor_class, entity_type, sensor_attribute, model_filter in ROBOT_BINARY_SENSORS:
                if model_filter is not None and not model_filter(robot):
                    continue
                cls = sensor_class or LitterRobotBinarySensor
                entities.append(
                    cls(
                        robot=robot,
                        entity_type=entity_type,
                        hub=hub,
                        sensor_attribute=sensor_attribute,
                    )
                )
        elif is_feeder_robot(robot):
            entities.append(
                LitterRobotDiagnosticBinarySensor(
                    robot=robot,
                    entity_type="Online",
                    hub=hub,
                    sensor_attribute="is_online",
                )
            )

    async_add_entities(entities, True)
