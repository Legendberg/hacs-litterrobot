"""Tests for the Litter-Robot binary sensor platform."""
from unittest.mock import MagicMock

import pytest

from custom_components.litterrobot.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    FEEDER_BINARY_SENSOR_DESCRIPTIONS,
    LitterRobotBinarySensor,
)


class TestBinarySensorDescriptions:
    """Tests for binary sensor descriptions."""

    def test_descriptions_count(self):
        """Verify expected number of binary sensor descriptions."""
        assert len(BINARY_SENSOR_DESCRIPTIONS) == 6

    def test_feeder_descriptions_count(self):
        assert len(FEEDER_BINARY_SENSOR_DESCRIPTIONS) == 1

    def test_drawer_removed_description(self):
        desc = BINARY_SENSOR_DESCRIPTIONS[0]
        assert desc.key == "drawer_removed"
        assert desc.robot_attr == "is_drawer_removed"

    def test_online_description(self):
        desc = BINARY_SENSOR_DESCRIPTIONS[4]
        assert desc.key == "online"
        assert desc.robot_attr == "is_online"


class TestLitterRobotBinarySensor:
    """Tests for LitterRobotBinarySensor entity."""

    def test_drawer_removed_off(self, mock_litter_robot, mock_hub):
        """Test drawer removed sensor is off."""
        desc = BINARY_SENSOR_DESCRIPTIONS[0]  # drawer_removed
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is False

    def test_drawer_removed_on(self, mock_litter_robot, mock_hub):
        """Test drawer removed sensor is on."""
        mock_litter_robot.is_drawer_removed = True
        desc = BINARY_SENSOR_DESCRIPTIONS[0]
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is True

    def test_bonnet_removed(self, mock_litter_robot, mock_hub):
        """Test bonnet removed sensor."""
        desc = BINARY_SENSOR_DESCRIPTIONS[1]  # bonnet_removed
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is False

    def test_laser_dirty(self, mock_litter_robot, mock_hub):
        """Test laser dirty sensor."""
        desc = BINARY_SENSOR_DESCRIPTIONS[2]  # laser_dirty
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is False

    def test_camera_audio_icon_on(self, mock_litter_robot, mock_hub):
        """Test camera audio icon when enabled."""
        desc = BINARY_SENSOR_DESCRIPTIONS[3]  # camera_audio
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is True
        assert sensor.icon == "mdi:microphone"

    def test_camera_audio_icon_off(self, mock_litter_robot, mock_hub):
        """Test camera audio icon when disabled."""
        mock_litter_robot.camera_audio_enabled = False
        desc = BINARY_SENSOR_DESCRIPTIONS[3]
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is False
        assert sensor.icon == "mdi:microphone-off"

    def test_online_sensor(self, mock_litter_robot, mock_hub):
        """Test online binary sensor."""
        desc = BINARY_SENSOR_DESCRIPTIONS[4]  # online
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is True

    def test_smart_weight_sensor(self, mock_litter_robot, mock_hub):
        """Test smart weight binary sensor."""
        desc = BINARY_SENSOR_DESCRIPTIONS[5]  # smart_weight
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.is_on is True

    def test_feeder_online(self, mock_feeder_robot, mock_hub):
        """Test feeder online binary sensor."""
        desc = FEEDER_BINARY_SENSOR_DESCRIPTIONS[0]
        sensor = LitterRobotBinarySensor(mock_feeder_robot, mock_hub, desc)
        assert sensor.is_on is True

    def test_no_icon_fn(self, mock_litter_robot, mock_hub):
        """Test binary sensor without icon_fn returns None."""
        desc = BINARY_SENSOR_DESCRIPTIONS[0]  # drawer_removed (no icon_fn)
        sensor = LitterRobotBinarySensor(mock_litter_robot, mock_hub, desc)
        assert sensor.icon is None
