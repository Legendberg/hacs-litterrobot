"""Support for Litter-Robot sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from pylitterbot import Pet
from pylitterbot.robot import Robot

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .entity import (
    LitterRobotEntity,
    LitterRobotEntityDescription,
    is_litter_robot,
    is_feeder_robot,
    is_lr5,
)
from .hub import LitterRobotHub


def icon_for_gauge_level(gauge_level: int | None = None, offset: int = 0) -> str:
    """Return a gauge icon valid identifier."""
    if gauge_level is None or gauge_level <= 0 + offset:
        return "mdi:gauge-empty"
    if gauge_level > 70 + offset:
        return "mdi:gauge-full"
    if gauge_level > 30 + offset:
        return "mdi:gauge"
    return "mdi:gauge-low"


def _wifi_icon(rssi: Any) -> str:
    """Return WiFi signal strength icon."""
    if rssi is None or rssi == 0:
        return "mdi:wifi-off"
    if rssi >= -50:
        return "mdi:wifi-strength-4"
    if rssi >= -60:
        return "mdi:wifi-strength-3"
    if rssi >= -70:
        return "mdi:wifi-strength-2"
    return "mdi:wifi-strength-1"


def _volume_icon(vol: Any) -> str:
    """Return volume icon."""
    if vol is None or vol == 0:
        return "mdi:volume-off"
    if vol < 50:
        return "mdi:volume-medium"
    return "mdi:volume-high"


# --- Robot Sensor Descriptions ---


@dataclass(frozen=True, kw_only=True)
class LitterRobotSensorDescription(
    SensorEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot sensor."""

    value_fn: Callable[[Robot], Any] | None = None
    icon_fn: Callable[[Any], str] | None = None


ROBOT_SENSOR_DESCRIPTIONS: tuple[LitterRobotSensorDescription, ...] = (
    LitterRobotSensorDescription(
        key="waste_drawer",
        entity_type="Waste Drawer",
        robot_attr="waste_drawer_level",
        native_unit_of_measurement=PERCENTAGE,
        icon_fn=lambda v: icon_for_gauge_level(v, 10),
    ),
    LitterRobotSensorDescription(
        key="litter_level",
        entity_type="Litter Level",
        robot_attr="litter_level",
        native_unit_of_measurement=PERCENTAGE,
        model_filter=is_lr5,
        icon_fn=icon_for_gauge_level,
    ),
    LitterRobotSensorDescription(
        key="total_clean_cycles",
        entity_type="Total Clean Cycles",
        robot_attr="cycle_count",
        icon="mdi:counter",
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="last_pet_weight",
        entity_type="Last Pet Weight",
        robot_attr="pet_weight",
        native_unit_of_measurement="lbs",
        icon="mdi:scale",
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="wifi_signal",
        entity_type="WiFi Signal",
        robot_attr="wifi_rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        model_filter=is_lr5,
        icon_fn=_wifi_icon,
    ),
    LitterRobotSensorDescription(
        key="sound_volume",
        entity_type="Sound Volume",
        robot_attr="sound_volume",
        native_unit_of_measurement="%",
        model_filter=is_lr5,
        icon_fn=_volume_icon,
    ),
    LitterRobotSensorDescription(
        key="firmware",
        entity_type="Firmware",
        robot_attr="firmware",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="total_scoops_saved",
        entity_type="Total Scoops Saved",
        robot_attr="scoops_saved_count",
        icon="mdi:hand-heart",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="next_filter_replacement",
        entity_type="Next Filter Replacement",
        robot_attr="next_filter_replacement_date",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="setup_date",
        entity_type="Setup Date",
        robot_attr="setup_date",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="last_cloud_checkin",
        entity_type="Last Cloud Check-in",
        robot_attr="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="drawer_empty_cycles",
        entity_type="Drawer Empty Cycles",
        robot_attr="odometer_empty_cycles",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="filter_change_cycles",
        entity_type="Filter Change Cycles",
        robot_attr="odometer_filter_cycles",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="power_cycles",
        entity_type="Power Cycles",
        robot_attr="odometer_power_cycles",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="cycles_since_reset",
        entity_type="Cycles Since Reset",
        robot_attr="last_reset_odometer_clean_cycles",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
    ),
    LitterRobotSensorDescription(
        key="hopper_status",
        entity_type="Hopper Status",
        robot_attr="hopper_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.hopper_status) if r.hopper_status is not None else None,
    ),
    LitterRobotSensorDescription(
        key="motor_fault_status",
        entity_type="Motor Fault Status",
        robot_attr="globe_motor_fault_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.globe_motor_fault_status) if r.globe_motor_fault_status is not None else None,
    ),
    LitterRobotSensorDescription(
        key="pinch_status",
        entity_type="Pinch Status",
        robot_attr="pinch_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.pinch_status) if r.pinch_status is not None else None,
    ),
    LitterRobotSensorDescription(
        key="cat_detect_status",
        entity_type="Cat Detect Status",
        robot_attr="cat_detect",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.cat_detect) if r.cat_detect is not None else None,
    ),
    LitterRobotSensorDescription(
        key="firmware_update_status",
        entity_type="Firmware Update Status",
        robot_attr="firmware_update_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.firmware_update_status) if r.firmware_update_status is not None else None,
    ),
    LitterRobotSensorDescription(
        key="mcu_update_status",
        entity_type="MCU Update Status",
        robot_attr="stm_update_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.stm_update_status) if r.stm_update_status is not None else None,
    ),
    LitterRobotSensorDescription(
        key="power_status",
        entity_type="Power Status",
        robot_attr="power_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.power_status) if r.power_status is not None else None,
    ),
    LitterRobotSensorDescription(
        key="privacy_mode",
        entity_type="Privacy Mode",
        robot_attr="privacy_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        model_filter=is_lr5,
        value_fn=lambda r: str(r.privacy_mode) if r.privacy_mode is not None else None,
    ),
)


class LitterRobotSensor(LitterRobotEntity, SensorEntity):
    """Generic Litter-Robot sensor driven by an entity description."""

    entity_description: LitterRobotSensorDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotSensorDescription,
    ) -> None:
        """Initialize a Litter-Robot sensor."""
        super().__init__(robot, description.entity_type, hub)
        self.entity_description = description
        self._sensor_attribute = description.robot_attr

    @property
    def native_value(self) -> Any:
        """Return the state."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.robot)
        return getattr(self.robot, self._sensor_attribute, None)

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        if self.entity_description.icon_fn:
            return self.entity_description.icon_fn(self.native_value)
        return self.entity_description.icon


class LitterRobotSleepTimeSensor(LitterRobotEntity, SensorEntity):
    """Litter-Robot sleep time sensor (returns None when sleep mode disabled)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        entity_type: str,
        sensor_attribute: str,
    ) -> None:
        """Initialize the sleep time sensor."""
        super().__init__(robot, entity_type, hub)
        self._sensor_attribute = sensor_attribute

    @property
    def native_value(self):
        """Return the state."""
        if self.robot.sleep_mode_enabled:
            return getattr(self.robot, self._sensor_attribute)
        return None


# --- Feeder Robot Sensor Descriptions ---


FEEDER_SENSOR_DESCRIPTIONS: tuple[LitterRobotSensorDescription, ...] = (
    LitterRobotSensorDescription(
        key="food_level",
        entity_type="Food Level",
        robot_attr="food_level",
        native_unit_of_measurement=PERCENTAGE,
        icon_fn=icon_for_gauge_level,
    ),
    LitterRobotSensorDescription(
        key="next_feeding",
        entity_type="Next Feeding",
        robot_attr="next_feeding",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
)


class FeederRobotFoodDispensedSensor(LitterRobotEntity, SensorEntity):
    """Feeder-Robot food dispensed today sensor (needs self.hass for timezone)."""

    def __init__(self, robot: Robot, hub: LitterRobotHub) -> None:
        """Initialize the food dispensed sensor."""
        super().__init__(robot, "Food Dispensed Today", hub)

    @property
    def native_value(self) -> float:
        """Return food dispensed today in cups."""
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(self.hass.config.time_zone)
        except Exception:
            tz = timezone.utc
        today_start = datetime.now(tz).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        try:
            return self.robot.get_food_dispensed_since(today_start)
        except Exception:
            return 0.0

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return "cups"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:bowl-mix"


class FeederRobotLastFeedingSensor(LitterRobotEntity, SensorEntity):
    """Feeder-Robot last feeding sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, robot: Robot, hub: LitterRobotHub) -> None:
        """Initialize the last feeding sensor."""
        super().__init__(robot, "Last Feeding", hub)

    @property
    def native_value(self):
        """Return the timestamp of the last feeding."""
        feeding = self.robot.last_feeding
        if feeding and "timestamp" in feeding:
            return feeding["timestamp"]
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return last feeding details."""
        feeding = self.robot.last_feeding
        if feeding:
            return {
                "amount": feeding.get("amount"),
                "name": feeding.get("name"),
            }
        return {}

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:food-drumstick"


# --- Pet Sensor Descriptions ---


@dataclass(frozen=True, kw_only=True)
class LitterRobotPetSensorDescription(SensorEntityDescription):
    """Describes a Litter-Robot pet sensor."""

    entity_type: str
    pet_attr: str = ""
    value_fn: Callable[[Pet], Any] | None = None
    icon_fn: Callable[[Any], str] | None = None


def _gender_icon(val: Any) -> str:
    """Return gender icon."""
    if val and str(val).lower() == "female":
        return "mdi:gender-female"
    return "mdi:gender-male"


def _pet_type_icon(val: Any) -> str:
    """Return pet type icon."""
    if val and str(val).lower() == "cat":
        return "mdi:cat"
    return "mdi:dog"


def _health_icon(val: Any) -> str:
    """Return health status icon."""
    return "mdi:heart-pulse" if val == "Healthy" else "mdi:alert-circle"


PET_SENSOR_DESCRIPTIONS: tuple[LitterRobotPetSensorDescription, ...] = (
    LitterRobotPetSensorDescription(
        key="pet_gender",
        entity_type="Gender",
        value_fn=lambda p: str(p.gender).capitalize() if getattr(p, "gender", None) else None,
        icon_fn=lambda v: _gender_icon(v),
    ),
    LitterRobotPetSensorDescription(
        key="pet_type",
        entity_type="Type",
        value_fn=lambda p: str(p.pet_type).capitalize() if getattr(p, "pet_type", None) else None,
        icon_fn=lambda v: _pet_type_icon(v),
    ),
    LitterRobotPetSensorDescription(
        key="pet_diet",
        entity_type="Diet",
        value_fn=lambda p: str(p.diet) if getattr(p, "diet", None) else None,
        icon="mdi:food-drumstick",
    ),
    LitterRobotPetSensorDescription(
        key="pet_environment",
        entity_type="Environment",
        value_fn=lambda p: str(p.environment_type) if getattr(p, "environment_type", None) else None,
        icon="mdi:home",
    ),
    LitterRobotPetSensorDescription(
        key="pet_birthday",
        entity_type="Birthday",
        value_fn=lambda p: p.birthday.isoformat() if getattr(p, "birthday", None) else None,
        icon="mdi:cake-variant-outline",
    ),
    LitterRobotPetSensorDescription(
        key="pet_adoption_date",
        entity_type="Adoption Date",
        value_fn=lambda p: p.adoption_date.isoformat() if getattr(p, "adoption_date", None) else None,
        icon="mdi:heart",
    ),
    LitterRobotPetSensorDescription(
        key="pet_fixed",
        entity_type="Fixed",
        value_fn=lambda p: ("Yes" if p.is_fixed else "No") if getattr(p, "is_fixed", None) is not None else None,
        icon="mdi:medical-bag",
    ),
)


class LitterRobotPetSensor(CoordinatorEntity, SensorEntity):
    """Base class for pet sensors."""

    def __init__(self, pet: Pet, entity_type: str, hub: LitterRobotHub) -> None:
        """Initialize the pet sensor."""
        super().__init__(hub.coordinator)
        self.pet = pet
        self.entity_type = entity_type

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self.pet.name} {self.entity_type}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.pet.id}-{self.entity_type.lower().replace(' ', '_')}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.pet.id)},
            "name": self.pet.name,
            "manufacturer": "Litter-Robot",
            "model": "Pet",
        }


class LitterRobotPetAttributeSensor(LitterRobotPetSensor):
    """Generic pet attribute sensor driven by a description."""

    def __init__(
        self,
        pet: Pet,
        hub: LitterRobotHub,
        description: LitterRobotPetSensorDescription,
    ) -> None:
        """Initialize the pet attribute sensor."""
        super().__init__(pet, description.entity_type, hub)
        self._description = description

    @property
    def native_value(self) -> Any:
        """Return the state."""
        if self._description.value_fn:
            return self._description.value_fn(self.pet)
        return getattr(self.pet, self._description.pet_attr, None)

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        if self._description.icon_fn:
            return self._description.icon_fn(self.native_value)
        return self._description.icon


class LitterRobotPetWeightSensor(LitterRobotPetSensor):
    """Pet weight sensor with full profile attributes."""

    @property
    def native_value(self) -> float | None:
        """Return the weight."""
        return self.pet.weight

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "lbs"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:scale"

    @property
    def extra_state_attributes(self) -> dict:
        """Return pet profile attributes."""
        attrs = {}
        attrs["estimated_weight"] = getattr(self.pet, "estimated_weight", None)
        attrs["last_weight_reading"] = getattr(self.pet, "last_weight_reading", None)
        pet_type = getattr(self.pet, "pet_type", None)
        attrs["pet_type"] = str(pet_type) if pet_type else None
        gender = getattr(self.pet, "gender", None)
        attrs["gender"] = str(gender) if gender else None
        breeds = getattr(self.pet, "breeds", None)
        attrs["breeds"] = ", ".join(breeds) if breeds else None
        attrs["age"] = getattr(self.pet, "age", None)
        birthday = getattr(self.pet, "birthday", None)
        attrs["birthday"] = birthday.isoformat() if birthday else None
        adoption_date = getattr(self.pet, "adoption_date", None)
        attrs["adoption_date"] = adoption_date.isoformat() if adoption_date else None
        diet = getattr(self.pet, "diet", None)
        attrs["diet"] = str(diet) if diet else None
        env = getattr(self.pet, "environment_type", None)
        attrs["environment"] = str(env) if env else None
        attrs["is_fixed"] = getattr(self.pet, "is_fixed", None)
        attrs["is_healthy"] = getattr(self.pet, "is_healthy", None)
        concerns = getattr(self.pet, "health_concerns", None)
        attrs["health_concerns"] = ", ".join(concerns) if concerns else None
        attrs["is_active"] = getattr(self.pet, "is_active", None)
        attrs["image_url"] = getattr(self.pet, "image_url", None)
        attrs["pet_tag_id"] = getattr(self.pet, "pet_tag_id", None)
        attrs["weight_id_enabled"] = getattr(self.pet, "weight_id_feature_enabled", None)
        return attrs


class LitterRobotPetVisitsSensor(LitterRobotPetSensor):
    """Pet visits sensor with configurable period (needs self.hass for timezone)."""

    def __init__(self, pet: Pet, entity_type: str, hub: LitterRobotHub, period: str = "today") -> None:
        """Initialize with a time period."""
        super().__init__(pet=pet, entity_type=entity_type, hub=hub)
        self._period = period

    def _get_period_start(self) -> datetime:
        """Return the start datetime for the configured period in the HA local timezone."""
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(self.hass.config.time_zone)
        except Exception:
            tz = timezone.utc
        now = datetime.now(tz)
        if self._period == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self._period == "week":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start -= timedelta(days=start.weekday())
            return start
        elif self._period == "month":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self._period == "year":
            return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @property
    def native_value(self) -> int:
        """Return visits for the period."""
        try:
            start = self._get_period_start()
            visits = self.pet.get_visits_since(start)
            if isinstance(visits, int):
                return visits
            return len(visits) if visits else 0
        except Exception:
            return 0

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:paw"


class LitterRobotPetWeightHistorySensor(LitterRobotPetSensor):
    """Pet weight history sensor showing recent readings."""

    @property
    def native_value(self) -> int:
        """Return the number of weight history entries available."""
        history = getattr(self.pet, "weight_history", [])
        return len(history)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:chart-line"

    @property
    def extra_state_attributes(self) -> dict:
        """Return recent weight history entries."""
        history = getattr(self.pet, "weight_history", [])
        entries = []
        for entry in history[:50]:
            entries.append({
                "timestamp": entry.timestamp.isoformat(),
                "weight": round(entry.weight, 2),
            })
        attrs = {"readings": len(history)}
        if entries:
            attrs["latest"] = entries[0]["weight"] if entries else None
            attrs["history"] = entries
        return attrs


class LitterRobotPetProfileSensor(LitterRobotPetSensor):
    """Pet profile sensor showing key info."""

    @property
    def native_value(self) -> str | None:
        """Return the pet type and breed."""
        pet_type = getattr(self.pet, "pet_type", None)
        breeds = getattr(self.pet, "breeds", None)
        if breeds:
            return ", ".join(breeds)
        return str(pet_type) if pet_type else None

    @property
    def icon(self) -> str:
        """Return the icon."""
        pet_type = getattr(self.pet, "pet_type", None)
        return "mdi:cat" if pet_type and str(pet_type) == "cat" else "mdi:dog"

    @property
    def extra_state_attributes(self) -> dict:
        """Return pet profile attributes."""
        attrs = {}
        pet_type = getattr(self.pet, "pet_type", None)
        attrs["pet_type"] = str(pet_type) if pet_type else None
        gender = getattr(self.pet, "gender", None)
        attrs["gender"] = str(gender) if gender else None
        breeds = getattr(self.pet, "breeds", None)
        attrs["breeds"] = ", ".join(breeds) if breeds else None
        attrs["age"] = getattr(self.pet, "age", None)
        birthday = getattr(self.pet, "birthday", None)
        attrs["birthday"] = birthday.isoformat() if birthday else None
        adoption_date = getattr(self.pet, "adoption_date", None)
        attrs["adoption_date"] = adoption_date.isoformat() if adoption_date else None
        diet = getattr(self.pet, "diet", None)
        attrs["diet"] = str(diet) if diet else None
        env = getattr(self.pet, "environment_type", None)
        attrs["environment"] = str(env) if env else None
        attrs["is_fixed"] = getattr(self.pet, "is_fixed", None)
        attrs["is_healthy"] = getattr(self.pet, "is_healthy", None)
        concerns = getattr(self.pet, "health_concerns", None)
        attrs["health_concerns"] = ", ".join(concerns) if concerns else None
        attrs["is_active"] = getattr(self.pet, "is_active", None)
        attrs["image_url"] = getattr(self.pet, "image_url", None)
        attrs["pet_tag_id"] = getattr(self.pet, "pet_tag_id", None)
        attrs["weight_id_enabled"] = getattr(self.pet, "weight_id_feature_enabled", None)
        return attrs


class LitterRobotPetAgeSensor(LitterRobotPetSensor):
    """Pet age sensor, calculated from birthday."""

    @property
    def native_value(self) -> int | None:
        """Return the age calculated from birthday."""
        birthday = getattr(self.pet, "birthday", None)
        if birthday:
            today = date.today()
            age = today.year - birthday.year
            if (today.month, today.day) < (birthday.month, birthday.day):
                age -= 1
            return age
        return getattr(self.pet, "age", None)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "years"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:cake-variant"

    @property
    def extra_state_attributes(self) -> dict:
        """Return birthday."""
        birthday = getattr(self.pet, "birthday", None)
        return {"birthday": birthday.isoformat() if birthday else None}


class LitterRobotPetHealthySensor(LitterRobotPetSensor):
    """Pet healthy status sensor."""

    @property
    def native_value(self) -> str | None:
        """Return health status."""
        is_healthy = getattr(self.pet, "is_healthy", None)
        if is_healthy is None:
            return None
        return "Healthy" if is_healthy else "Needs attention"

    @property
    def icon(self) -> str:
        """Return the icon."""
        is_healthy = getattr(self.pet, "is_healthy", None)
        return "mdi:heart-pulse" if is_healthy else "mdi:alert-circle"

    @property
    def extra_state_attributes(self) -> dict:
        """Return health concerns."""
        concerns = getattr(self.pet, "health_concerns", None)
        return {"health_concerns": ", ".join(concerns) if concerns else None}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot sensors using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for robot in hub.account.robots:
        if is_litter_robot(robot):
            # Description-driven robot sensors
            for desc in ROBOT_SENSOR_DESCRIPTIONS:
                if desc.model_filter and not desc.model_filter(robot):
                    continue
                entities.append(LitterRobotSensor(robot, hub, desc))
            # Custom sleep time sensors
            entities.append(
                LitterRobotSleepTimeSensor(
                    robot, hub, "Sleep Mode Start Time", "sleep_mode_start_time"
                )
            )
            entities.append(
                LitterRobotSleepTimeSensor(
                    robot, hub, "Sleep Mode End Time", "sleep_mode_end_time"
                )
            )
        elif is_feeder_robot(robot):
            # Description-driven feeder sensors
            for desc in FEEDER_SENSOR_DESCRIPTIONS:
                entities.append(LitterRobotSensor(robot, hub, desc))
            # Custom feeder sensors
            entities.append(FeederRobotFoodDispensedSensor(robot, hub))
            entities.append(FeederRobotLastFeedingSensor(robot, hub))

    # Pet sensors
    for pet in hub.account.pets:
        entities.append(
            LitterRobotPetWeightSensor(pet=pet, entity_type="Weight", hub=hub)
        )
        entities.append(
            LitterRobotPetVisitsSensor(pet=pet, entity_type="Visits Today", hub=hub, period="today")
        )
        entities.append(
            LitterRobotPetVisitsSensor(pet=pet, entity_type="Visits This Week", hub=hub, period="week")
        )
        entities.append(
            LitterRobotPetVisitsSensor(pet=pet, entity_type="Visits This Month", hub=hub, period="month")
        )
        entities.append(
            LitterRobotPetVisitsSensor(pet=pet, entity_type="Visits This Year", hub=hub, period="year")
        )
        entities.append(
            LitterRobotPetWeightHistorySensor(pet=pet, entity_type="Weight History", hub=hub)
        )
        entities.append(
            LitterRobotPetProfileSensor(pet=pet, entity_type="Profile", hub=hub)
        )
        # Description-driven simple pet sensors
        for desc in PET_SENSOR_DESCRIPTIONS:
            entities.append(LitterRobotPetAttributeSensor(pet, hub, desc))
        entities.append(
            LitterRobotPetAgeSensor(pet=pet, entity_type="Age", hub=hub)
        )
        entities.append(
            LitterRobotPetHealthySensor(pet=pet, entity_type="Health", hub=hub)
        )

    async_add_entities(entities, True)
