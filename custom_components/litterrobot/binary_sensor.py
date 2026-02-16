"""Support for Litter-Robot binary sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pylitterbot.robot import Robot

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import (
    LitterRobotEntity,
    LitterRobotEntityDescription,
    is_litter_robot,
    is_feeder_robot,
    is_lr5,
    is_lr5_pro,
)
from .hub import LitterRobotHub


@dataclass(frozen=True, kw_only=True)
class LitterRobotBinarySensorDescription(
    BinarySensorEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot binary sensor."""

    icon_fn: Callable[[bool], str] | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[LitterRobotBinarySensorDescription, ...] = (
    LitterRobotBinarySensorDescription(
        key="drawer_removed",
        entity_type="Drawer Removed",
        robot_attr="is_drawer_removed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        model_filter=is_lr5,
    ),
    LitterRobotBinarySensorDescription(
        key="bonnet_removed",
        entity_type="Bonnet Removed",
        robot_attr="is_bonnet_removed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        model_filter=is_lr5,
    ),
    LitterRobotBinarySensorDescription(
        key="laser_dirty",
        entity_type="Laser Dirty",
        robot_attr="is_laser_dirty",
        device_class=BinarySensorDeviceClass.PROBLEM,
        model_filter=is_lr5,
    ),
    LitterRobotBinarySensorDescription(
        key="camera_audio",
        entity_type="Camera Audio",
        robot_attr="camera_audio_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5_pro,
        icon_fn=lambda v: "mdi:microphone" if v else "mdi:microphone-off",
    ),
    LitterRobotBinarySensorDescription(
        key="online",
        entity_type="Online",
        robot_attr="is_online",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotBinarySensorDescription(
        key="smart_weight",
        entity_type="Smart Weight",
        robot_attr="is_smart_weight_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
)

FEEDER_BINARY_SENSOR_DESCRIPTIONS: tuple[LitterRobotBinarySensorDescription, ...] = (
    LitterRobotBinarySensorDescription(
        key="feeder_online",
        entity_type="Online",
        robot_attr="is_online",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


class LitterRobotBinarySensor(LitterRobotEntity, BinarySensorEntity):
    """Litter-Robot binary sensor driven by an entity description."""

    entity_description: LitterRobotBinarySensorDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotBinarySensorDescription,
    ) -> None:
        """Initialize a Litter-Robot binary sensor."""
        super().__init__(robot, description.entity_type, hub)
        self.entity_description = description
        self._sensor_attribute = description.robot_attr

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return getattr(self.robot, self._sensor_attribute, False)

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        if self.entity_description.icon_fn:
            return self.entity_description.icon_fn(self.is_on)
        return None


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
            for desc in BINARY_SENSOR_DESCRIPTIONS:
                if desc.model_filter and not desc.model_filter(robot):
                    continue
                entities.append(LitterRobotBinarySensor(robot, hub, desc))
        elif is_feeder_robot(robot):
            for desc in FEEDER_BINARY_SENSOR_DESCRIPTIONS:
                entities.append(LitterRobotBinarySensor(robot, hub, desc))

    async_add_entities(entities, True)
