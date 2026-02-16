"""Support for Litter-Robot sensors."""
from __future__ import annotations

from typing import Callable

from pylitterbot.robot import Robot

from datetime import datetime, timezone

from pylitterbot import Pet

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .entity import LitterRobotEntity, is_litter_robot, is_feeder_robot, is_lr5
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


class LitterRobotPropertySensor(LitterRobotEntity, SensorEntity):
    """Litter-Robot property sensor."""

    def __init__(
        self, robot: Robot, entity_type: str, hub: LitterRobotHub, sensor_attribute: str
    ) -> None:
        """Pass robot, entity_type and hub to LitterRobotEntity."""
        super().__init__(robot, entity_type, hub)
        self.sensor_attribute = sensor_attribute

    @property
    def native_value(self) -> str:
        """Return the state."""
        return getattr(self.robot, self.sensor_attribute)


class LitterRobotWasteSensor(LitterRobotPropertySensor):
    """Litter-Robot waste sensor."""

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return PERCENTAGE

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        return icon_for_gauge_level(self.native_value, 10)


class LitterRobotSleepTimeSensor(LitterRobotPropertySensor):
    """Litter-Robot sleep time sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Return the state."""
        if self.robot.sleep_mode_enabled:
            return getattr(self.robot, self.sensor_attribute)
        return None


class LitterRobotLitterLevelSensor(LitterRobotPropertySensor):
    """Litter-Robot 5 litter level sensor."""

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return PERCENTAGE

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        return icon_for_gauge_level(self.native_value)


class LitterRobotCycleCountSensor(LitterRobotPropertySensor):
    """Litter-Robot 5 cycle count sensor."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:counter"


class LitterRobotPetWeightSensor(LitterRobotPropertySensor):
    """Litter-Robot 5 pet weight sensor."""

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return "lbs"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:scale"


class LitterRobotWifiSensor(LitterRobotPropertySensor):
    """Litter-Robot 5 WiFi signal strength sensor."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    @property
    def icon(self) -> str:
        """Return the icon."""
        rssi = self.native_value
        if rssi is None or rssi == 0:
            return "mdi:wifi-off"
        if rssi >= -50:
            return "mdi:wifi-strength-4"
        if rssi >= -60:
            return "mdi:wifi-strength-3"
        if rssi >= -70:
            return "mdi:wifi-strength-2"
        return "mdi:wifi-strength-1"


class LitterRobotSoundVolumeSensor(LitterRobotPropertySensor):
    """Litter-Robot 5 sound volume sensor."""

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return "%"

    @property
    def icon(self) -> str:
        """Return the icon."""
        vol = self.native_value
        if vol is None or vol == 0:
            return "mdi:volume-off"
        if vol < 50:
            return "mdi:volume-medium"
        return "mdi:volume-high"


class LitterRobotFirmwareSensor(LitterRobotPropertySensor):
    """Litter-Robot 5 firmware version sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:chip"


class LitterRobotDiagnosticSensor(LitterRobotPropertySensor):
    """Litter-Robot diagnostic sensor (generic text value)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Return the state."""
        value = getattr(self.robot, self.sensor_attribute, None)
        return str(value) if value is not None else None


class LitterRobotDiagnosticCounterSensor(LitterRobotPropertySensor):
    """Litter-Robot diagnostic counter sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:counter"


class LitterRobotDiagnosticTimestampSensor(LitterRobotPropertySensor):
    """Litter-Robot diagnostic timestamp sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the state."""
        return getattr(self.robot, self.sensor_attribute, None)


class LitterRobotScoopsSavedSensor(LitterRobotPropertySensor):
    """Litter-Robot 5 scoops saved sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:hand-heart"


ROBOT_SENSORS: list[
    tuple[type[LitterRobotPropertySensor], str, str, Callable[[Robot], bool] | None]
] = [
    (LitterRobotWasteSensor, "Waste Drawer", "waste_drawer_level", None),
    (LitterRobotSleepTimeSensor, "Sleep Mode Start Time", "sleep_mode_start_time", None),
    (LitterRobotSleepTimeSensor, "Sleep Mode End Time", "sleep_mode_end_time", None),
    (LitterRobotLitterLevelSensor, "Litter Level", "litter_level", is_lr5),
    (LitterRobotCycleCountSensor, "Total Clean Cycles", "cycle_count", is_lr5),
    (LitterRobotPetWeightSensor, "Last Pet Weight", "pet_weight", is_lr5),
    (LitterRobotWifiSensor, "WiFi Signal", "wifi_rssi", is_lr5),
    (LitterRobotSoundVolumeSensor, "Sound Volume", "sound_volume", is_lr5),
    (LitterRobotFirmwareSensor, "Firmware", "firmware", is_lr5),
    (LitterRobotScoopsSavedSensor, "Total Scoops Saved", "scoops_saved_count", is_lr5),
    (LitterRobotDiagnosticTimestampSensor, "Next Filter Replacement", "next_filter_replacement_date", is_lr5),
    (LitterRobotDiagnosticTimestampSensor, "Setup Date", "setup_date", is_lr5),
    (LitterRobotDiagnosticTimestampSensor, "Last Cloud Check-in", "last_seen", is_lr5),
    (LitterRobotDiagnosticCounterSensor, "Drawer Empty Cycles", "odometer_empty_cycles", is_lr5),
    (LitterRobotDiagnosticCounterSensor, "Filter Change Cycles", "odometer_filter_cycles", is_lr5),
    (LitterRobotDiagnosticCounterSensor, "Power Cycles", "odometer_power_cycles", is_lr5),
    (LitterRobotDiagnosticCounterSensor, "Cycles Since Reset", "last_reset_odometer_clean_cycles", is_lr5),
    (LitterRobotDiagnosticSensor, "Hopper Status", "hopper_status", is_lr5),
    (LitterRobotDiagnosticSensor, "Motor Fault Status", "globe_motor_fault_status", is_lr5),
    (LitterRobotDiagnosticSensor, "Pinch Status", "pinch_status", is_lr5),
    (LitterRobotDiagnosticSensor, "Cat Detect Status", "cat_detect", is_lr5),
    (LitterRobotDiagnosticSensor, "Firmware Update Status", "firmware_update_status", is_lr5),
    (LitterRobotDiagnosticSensor, "MCU Update Status", "stm_update_status", is_lr5),
    (LitterRobotDiagnosticSensor, "Power Status", "power_status", is_lr5),
    (LitterRobotDiagnosticSensor, "Privacy Mode", "privacy_mode", is_lr5),
]


class LitterRobotPetSensor(CoordinatorEntity, SensorEntity):
    """A pet sensor base class."""

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


class LitterRobotPetWeightSensor(LitterRobotPetSensor):
    """Pet weight sensor."""

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
    """Pet visits sensor with configurable period."""

    def __init__(self, pet, entity_type: str, hub, period: str = "today") -> None:
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
            from datetime import timedelta
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


class LitterRobotPetGenderSensor(LitterRobotPetSensor):
    """Pet gender sensor."""

    @property
    def native_value(self) -> str | None:
        """Return the gender."""
        gender = getattr(self.pet, "gender", None)
        return str(gender).capitalize() if gender else None

    @property
    def icon(self) -> str:
        """Return the icon."""
        gender = getattr(self.pet, "gender", None)
        if gender and str(gender) == "female":
            return "mdi:gender-female"
        return "mdi:gender-male"


class LitterRobotPetAgeSensor(LitterRobotPetSensor):
    """Pet age sensor, calculated from birthday."""

    @property
    def native_value(self) -> int | None:
        """Return the age calculated from birthday."""
        birthday = getattr(self.pet, "birthday", None)
        if birthday:
            from datetime import date
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


class LitterRobotPetDietSensor(LitterRobotPetSensor):
    """Pet diet sensor."""

    @property
    def native_value(self) -> str | None:
        """Return the diet."""
        diet = getattr(self.pet, "diet", None)
        return str(diet) if diet else None

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:food-drumstick"


class LitterRobotPetEnvironmentSensor(LitterRobotPetSensor):
    """Pet environment sensor."""

    @property
    def native_value(self) -> str | None:
        """Return the environment type."""
        env = getattr(self.pet, "environment_type", None)
        return str(env) if env else None

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:home"


class LitterRobotPetTypeSensor(LitterRobotPetSensor):
    """Pet type sensor (Cat/Dog)."""

    @property
    def native_value(self) -> str | None:
        """Return the pet type."""
        pet_type = getattr(self.pet, "pet_type", None)
        return str(pet_type).capitalize() if pet_type else None

    @property
    def icon(self) -> str:
        """Return the icon."""
        pet_type = getattr(self.pet, "pet_type", None)
        return "mdi:cat" if pet_type and str(pet_type) == "cat" else "mdi:dog"


class LitterRobotPetBirthdaySensor(LitterRobotPetSensor):
    """Pet birthday sensor."""

    @property
    def native_value(self) -> str | None:
        """Return the birthday."""
        birthday = getattr(self.pet, "birthday", None)
        return birthday.isoformat() if birthday else None

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:cake-variant-outline"


class LitterRobotPetAdoptionDateSensor(LitterRobotPetSensor):
    """Pet adoption date sensor."""

    @property
    def native_value(self) -> str | None:
        """Return the adoption date."""
        adoption_date = getattr(self.pet, "adoption_date", None)
        return adoption_date.isoformat() if adoption_date else None

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:heart"


class LitterRobotPetFixedSensor(LitterRobotPetSensor):
    """Pet fixed/neutered sensor."""

    @property
    def native_value(self) -> str | None:
        """Return fixed status."""
        is_fixed = getattr(self.pet, "is_fixed", None)
        if is_fixed is None:
            return None
        return "Yes" if is_fixed else "No"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:medical-bag"


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


class FeederRobotFoodLevelSensor(LitterRobotPropertySensor):
    """Feeder-Robot food level sensor."""

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return PERCENTAGE

    @property
    def icon(self) -> str:
        """Return the icon."""
        return icon_for_gauge_level(self.native_value)


class FeederRobotFoodDispensedSensor(LitterRobotPropertySensor):
    """Feeder-Robot food dispensed today sensor."""

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


class FeederRobotLastFeedingSensor(LitterRobotPropertySensor):
    """Feeder-Robot last feeding sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

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


class FeederRobotNextFeedingSensor(LitterRobotPropertySensor):
    """Feeder-Robot next feeding sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Return the next feeding time."""
        return getattr(self.robot, self.sensor_attribute, None)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:clock-outline"


FEEDER_SENSORS: list[
    tuple[type[LitterRobotPropertySensor], str, str]
] = [
    (FeederRobotFoodLevelSensor, "Food Level", "food_level"),
    (FeederRobotFoodDispensedSensor, "Food Dispensed Today", "food_dispensed_today"),
    (FeederRobotLastFeedingSensor, "Last Feeding", "last_feeding"),
    (FeederRobotNextFeedingSensor, "Next Feeding", "next_feeding"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot sensors using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if is_litter_robot(robot):
            for sensor_class, entity_type, sensor_attribute, model_filter in ROBOT_SENSORS:
                if model_filter is not None and not model_filter(robot):
                    continue
                entities.append(
                    sensor_class(
                        robot=robot,
                        entity_type=entity_type,
                        hub=hub,
                        sensor_attribute=sensor_attribute,
                    )
                )
        elif is_feeder_robot(robot):
            for sensor_class, entity_type, sensor_attribute in FEEDER_SENSORS:
                entities.append(
                    sensor_class(
                        robot=robot,
                        entity_type=entity_type,
                        hub=hub,
                        sensor_attribute=sensor_attribute,
                    )
                )

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
        entities.append(
            LitterRobotPetGenderSensor(pet=pet, entity_type="Gender", hub=hub)
        )
        entities.append(
            LitterRobotPetAgeSensor(pet=pet, entity_type="Age", hub=hub)
        )
        entities.append(
            LitterRobotPetDietSensor(pet=pet, entity_type="Diet", hub=hub)
        )
        entities.append(
            LitterRobotPetEnvironmentSensor(pet=pet, entity_type="Environment", hub=hub)
        )
        entities.append(
            LitterRobotPetTypeSensor(pet=pet, entity_type="Type", hub=hub)
        )
        entities.append(
            LitterRobotPetBirthdaySensor(pet=pet, entity_type="Birthday", hub=hub)
        )
        entities.append(
            LitterRobotPetAdoptionDateSensor(pet=pet, entity_type="Adoption Date", hub=hub)
        )
        entities.append(
            LitterRobotPetFixedSensor(pet=pet, entity_type="Fixed", hub=hub)
        )
        entities.append(
            LitterRobotPetHealthySensor(pet=pet, entity_type="Health", hub=hub)
        )

    async_add_entities(entities, True)
