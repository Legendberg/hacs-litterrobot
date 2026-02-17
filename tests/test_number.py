"""Tests for the Litter-Robot number platform."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.number import (
    NUMBER_DESCRIPTIONS,
    LitterRobotNumber,
)


class TestNumberDescriptions:
    """Tests for number descriptions."""

    def test_descriptions_count(self):
        assert len(NUMBER_DESCRIPTIONS) == 1

    def test_night_light_brightness_description(self):
        desc = NUMBER_DESCRIPTIONS[0]
        assert desc.key == "night_light_brightness"
        assert desc.entity_type == "Night Light Brightness"
        assert desc.min_value == 0
        assert desc.max_value == 100
        assert desc.step == 1
        assert desc.icon == "mdi:brightness-percent"


class TestLitterRobotNumber:
    """Tests for LitterRobotNumber entity."""

    def test_native_value(self, mock_litter_robot, mock_hub):
        """Test night light brightness returns correct value."""
        desc = NUMBER_DESCRIPTIONS[0]
        number = LitterRobotNumber(mock_litter_robot, mock_hub, desc)
        assert number.native_value == 75.0

    def test_min_max_step(self, mock_litter_robot, mock_hub):
        """Test min, max, and step values are set correctly."""
        desc = NUMBER_DESCRIPTIONS[0]
        number = LitterRobotNumber(mock_litter_robot, mock_hub, desc)
        assert number.native_min_value == 0
        assert number.native_max_value == 100
        assert number.native_step == 1

    async def test_set_value(self, mock_litter_robot, mock_hub):
        """Test setting the brightness value."""
        desc = NUMBER_DESCRIPTIONS[0]
        number = LitterRobotNumber(mock_litter_robot, mock_hub, desc)
        number.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await number.async_set_native_value(50.0)

        mock_litter_robot.set_night_light_brightness.assert_awaited_once_with(50)
