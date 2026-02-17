"""Tests for the Litter-Robot sensor platform."""
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from custom_components.litterrobot.sensor import (
    icon_for_gauge_level,
    _wifi_icon,
    _volume_icon,
    _gender_icon,
    _pet_type_icon,
    _health_icon,
    ROBOT_SENSOR_DESCRIPTIONS,
    FEEDER_SENSOR_DESCRIPTIONS,
    PET_SENSOR_DESCRIPTIONS,
    LitterRobotSensor,
    LitterRobotSleepTimeSensor,
    FeederRobotFoodDispensedSensor,
    FeederRobotLastFeedingSensor,
    LitterRobotPetWeightSensor,
    LitterRobotPetVisitsSensor,
    LitterRobotPetWeightHistorySensor,
    LitterRobotPetProfileSensor,
    LitterRobotPetAgeSensor,
    LitterRobotPetHealthySensor,
    LitterRobotPetAttributeSensor,
)


# --- Icon function tests ---


class TestGaugeIcon:
    """Tests for icon_for_gauge_level."""

    def test_none(self):
        assert icon_for_gauge_level(None) == "mdi:gauge-empty"

    def test_zero(self):
        assert icon_for_gauge_level(0) == "mdi:gauge-empty"

    def test_low(self):
        assert icon_for_gauge_level(25) == "mdi:gauge-low"

    def test_medium(self):
        assert icon_for_gauge_level(50) == "mdi:gauge"

    def test_high(self):
        assert icon_for_gauge_level(80) == "mdi:gauge-full"

    def test_with_offset(self):
        assert icon_for_gauge_level(10, offset=10) == "mdi:gauge-empty"
        assert icon_for_gauge_level(50, offset=10) == "mdi:gauge"
        assert icon_for_gauge_level(85, offset=10) == "mdi:gauge-full"


class TestWifiIcon:
    """Tests for _wifi_icon."""

    def test_none(self):
        assert _wifi_icon(None) == "mdi:wifi-off"

    def test_zero(self):
        assert _wifi_icon(0) == "mdi:wifi-off"

    def test_excellent(self):
        assert _wifi_icon(-40) == "mdi:wifi-strength-4"

    def test_good(self):
        assert _wifi_icon(-55) == "mdi:wifi-strength-3"

    def test_fair(self):
        assert _wifi_icon(-65) == "mdi:wifi-strength-2"

    def test_weak(self):
        assert _wifi_icon(-80) == "mdi:wifi-strength-1"


class TestVolumeIcon:
    """Tests for _volume_icon."""

    def test_none(self):
        assert _volume_icon(None) == "mdi:volume-off"

    def test_zero(self):
        assert _volume_icon(0) == "mdi:volume-off"

    def test_medium(self):
        assert _volume_icon(40) == "mdi:volume-medium"

    def test_high(self):
        assert _volume_icon(75) == "mdi:volume-high"


class TestPetIcons:
    """Tests for pet icon functions."""

    def test_gender_female(self):
        assert _gender_icon("female") == "mdi:gender-female"

    def test_gender_male(self):
        assert _gender_icon("male") == "mdi:gender-male"

    def test_gender_none(self):
        assert _gender_icon(None) == "mdi:gender-male"

    def test_pet_type_cat(self):
        assert _pet_type_icon("cat") == "mdi:cat"

    def test_pet_type_dog(self):
        assert _pet_type_icon("dog") == "mdi:dog"

    def test_health_healthy(self):
        assert _health_icon("Healthy") == "mdi:heart-pulse"

    def test_health_not_healthy(self):
        assert _health_icon("Needs attention") == "mdi:alert-circle"


# --- Robot sensor description tests ---


class TestRobotSensorDescriptions:
    """Tests for ROBOT_SENSOR_DESCRIPTIONS."""

    def test_descriptions_count(self):
        """Verify we have the expected number of robot sensor descriptions."""
        assert len(ROBOT_SENSOR_DESCRIPTIONS) == 23

    def test_waste_drawer_description(self):
        desc = ROBOT_SENSOR_DESCRIPTIONS[0]
        assert desc.key == "waste_drawer"
        assert desc.entity_type == "Waste Drawer"
        assert desc.robot_attr == "waste_drawer_level"
        assert desc.native_unit_of_measurement == "%"

    def test_litter_level_description(self):
        desc = ROBOT_SENSOR_DESCRIPTIONS[1]
        assert desc.key == "litter_level"
        assert desc.entity_type == "Litter Level"
        assert desc.model_filter is not None

    def test_feeder_descriptions_count(self):
        assert len(FEEDER_SENSOR_DESCRIPTIONS) == 2


# --- Sensor entity tests ---


class TestLitterRobotSensor:
    """Tests for LitterRobotSensor entity."""

    def test_waste_drawer_value(self, mock_litter_robot, mock_hub):
        """Test waste drawer sensor returns correct value."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[0]  # waste_drawer
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        assert sensor.native_value == 50

    def test_waste_drawer_icon(self, mock_litter_robot, mock_hub):
        """Test waste drawer sensor returns correct icon."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[0]
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        # 50 with offset 10 -> gauge
        assert sensor.icon == "mdi:gauge"

    def test_litter_level_value(self, mock_litter_robot, mock_hub):
        """Test litter level sensor returns correct value."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[1]  # litter_level
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        assert sensor.native_value == 80

    def test_wifi_signal_value(self, mock_litter_robot, mock_hub):
        """Test WiFi signal sensor returns correct value."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[4]  # wifi_signal
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        assert sensor.native_value == -45

    def test_wifi_signal_icon(self, mock_litter_robot, mock_hub):
        """Test WiFi signal sensor returns correct icon."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[4]
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        assert sensor.icon == "mdi:wifi-strength-4"

    def test_sound_volume_value(self, mock_litter_robot, mock_hub):
        """Test sound volume sensor returns correct value."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[5]  # sound_volume
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        assert sensor.native_value == 75

    def test_firmware_value(self, mock_litter_robot, mock_hub):
        """Test firmware sensor returns correct value."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[6]  # firmware
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        assert sensor.native_value == "1.2.3.4"
        assert sensor.icon == "mdi:chip"

    def test_value_fn_sensor(self, mock_litter_robot, mock_hub):
        """Test sensor with value_fn returns processed value."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[15]  # hopper_status (has value_fn)
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        value = sensor.native_value
        assert value is not None

    def test_static_icon(self, mock_litter_robot, mock_hub):
        """Test sensor with static icon."""
        desc = ROBOT_SENSOR_DESCRIPTIONS[2]  # total_clean_cycles
        sensor = LitterRobotSensor(mock_litter_robot, mock_hub, desc)
        assert sensor.icon == "mdi:counter"


# --- Sleep time sensor tests ---


class TestSleepTimeSensor:
    """Tests for LitterRobotSleepTimeSensor."""

    def test_sleep_enabled_returns_value(self, mock_litter_robot, mock_hub):
        """Test sleep time sensor returns value when sleep mode enabled."""
        mock_litter_robot.sleep_mode_enabled = True
        sensor = LitterRobotSleepTimeSensor(
            mock_litter_robot, mock_hub, "Sleep Mode Start Time", "sleep_mode_start_time"
        )
        assert sensor.native_value == mock_litter_robot.sleep_mode_start_time

    def test_sleep_disabled_returns_none(self, mock_litter_robot, mock_hub):
        """Test sleep time sensor returns None when sleep mode disabled."""
        mock_litter_robot.sleep_mode_enabled = False
        sensor = LitterRobotSleepTimeSensor(
            mock_litter_robot, mock_hub, "Sleep Mode Start Time", "sleep_mode_start_time"
        )
        assert sensor.native_value is None


# --- Feeder sensor tests ---


class TestFeederSensors:
    """Tests for feeder-specific sensors."""

    def test_food_level_sensor(self, mock_feeder_robot, mock_hub):
        """Test food level sensor."""
        desc = FEEDER_SENSOR_DESCRIPTIONS[0]  # food_level
        sensor = LitterRobotSensor(mock_feeder_robot, mock_hub, desc)
        assert sensor.native_value == 60

    def test_last_feeding_sensor(self, mock_feeder_robot, mock_hub):
        """Test last feeding sensor returns timestamp."""
        sensor = FeederRobotLastFeedingSensor(mock_feeder_robot, mock_hub)
        assert sensor.native_value == mock_feeder_robot.last_feeding["timestamp"]

    def test_last_feeding_attributes(self, mock_feeder_robot, mock_hub):
        """Test last feeding sensor extra attributes."""
        sensor = FeederRobotLastFeedingSensor(mock_feeder_robot, mock_hub)
        attrs = sensor.extra_state_attributes
        assert attrs["amount"] == 0.25
        assert attrs["name"] == "Breakfast"

    def test_last_feeding_no_data(self, mock_feeder_robot, mock_hub):
        """Test last feeding sensor with no feeding data."""
        mock_feeder_robot.last_feeding = None
        sensor = FeederRobotLastFeedingSensor(mock_feeder_robot, mock_hub)
        assert sensor.native_value is None
        assert sensor.extra_state_attributes == {}


# --- Pet sensor tests ---


class TestPetSensors:
    """Tests for pet sensors."""

    def test_pet_weight_sensor(self, mock_pet, mock_hub):
        """Test pet weight sensor."""
        sensor = LitterRobotPetWeightSensor(
            pet=mock_pet, entity_type="Weight", hub=mock_hub
        )
        assert sensor.native_value == 10.5
        assert sensor.native_unit_of_measurement == "lbs"
        assert sensor.icon == "mdi:scale"

    def test_pet_weight_extra_attrs(self, mock_pet, mock_hub):
        """Test pet weight sensor extra attributes."""
        sensor = LitterRobotPetWeightSensor(
            pet=mock_pet, entity_type="Weight", hub=mock_hub
        )
        attrs = sensor.extra_state_attributes
        assert attrs["estimated_weight"] == 10.3
        assert attrs["breeds"] == "Domestic Shorthair"
        assert attrs["is_fixed"] is True

    def test_pet_visits_sensor(self, mock_pet, mock_hub):
        """Test pet visits sensor returns visit count."""
        sensor = LitterRobotPetVisitsSensor(
            pet=mock_pet, entity_type="Visits Today", hub=mock_hub, period="today"
        )
        sensor.hass = MagicMock()
        sensor.hass.config.time_zone = "UTC"
        assert sensor.native_value == 3
        assert sensor.icon == "mdi:paw"

    def test_pet_weight_history_sensor(self, mock_pet, mock_hub):
        """Test pet weight history sensor."""
        sensor = LitterRobotPetWeightHistorySensor(
            pet=mock_pet, entity_type="Weight History", hub=mock_hub
        )
        assert sensor.native_value == 2
        assert sensor.icon == "mdi:chart-line"
        attrs = sensor.extra_state_attributes
        assert attrs["readings"] == 2
        assert attrs["latest"] == 10.55

    def test_pet_profile_sensor(self, mock_pet, mock_hub):
        """Test pet profile sensor."""
        sensor = LitterRobotPetProfileSensor(
            pet=mock_pet, entity_type="Profile", hub=mock_hub
        )
        assert sensor.native_value == "Domestic Shorthair"
        assert sensor.icon == "mdi:cat"

    def test_pet_age_sensor(self, mock_pet, mock_hub):
        """Test pet age sensor calculated from birthday."""
        sensor = LitterRobotPetAgeSensor(
            pet=mock_pet, entity_type="Age", hub=mock_hub
        )
        # Birthday 2022-05-15, today is 2026-02-16 -> age 3
        assert sensor.native_value == 3
        assert sensor.native_unit_of_measurement == "years"
        assert sensor.icon == "mdi:cake-variant"

    def test_pet_healthy_sensor(self, mock_pet, mock_hub):
        """Test pet healthy sensor."""
        sensor = LitterRobotPetHealthySensor(
            pet=mock_pet, entity_type="Health", hub=mock_hub
        )
        assert sensor.native_value == "Healthy"
        assert sensor.icon == "mdi:heart-pulse"

    def test_pet_healthy_sensor_unhealthy(self, mock_pet, mock_hub):
        """Test pet healthy sensor when not healthy."""
        mock_pet.is_healthy = False
        sensor = LitterRobotPetHealthySensor(
            pet=mock_pet, entity_type="Health", hub=mock_hub
        )
        assert sensor.native_value == "Needs attention"
        assert sensor.icon == "mdi:alert-circle"

    def test_pet_unique_id(self, mock_pet, mock_hub):
        """Test pet sensor unique_id format."""
        sensor = LitterRobotPetWeightSensor(
            pet=mock_pet, entity_type="Weight", hub=mock_hub
        )
        assert sensor.unique_id == "pet-test-id-weight"

    def test_pet_device_info(self, mock_pet, mock_hub):
        """Test pet sensor device info."""
        sensor = LitterRobotPetWeightSensor(
            pet=mock_pet, entity_type="Weight", hub=mock_hub
        )
        info = sensor.device_info
        assert info["model"] == "Pet"
        assert info["name"] == "Test Cat"

    def test_pet_attribute_sensor(self, mock_pet, mock_hub):
        """Test description-driven pet attribute sensor."""
        desc = PET_SENSOR_DESCRIPTIONS[0]  # gender
        sensor = LitterRobotPetAttributeSensor(mock_pet, mock_hub, desc)
        value = sensor.native_value
        assert value is not None
