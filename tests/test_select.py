"""Tests for the Litter-Robot select platform."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.select import (
    ROBOT_SELECT_DESCRIPTIONS,
    FEEDER_SELECT_DESCRIPTIONS,
    LitterRobotSelect,
    _night_light_icon,
    _BRIGHTNESS_LABEL_TO_LEVEL,
    _BRIGHTNESS_LEVEL_TO_LABEL,
    _MEAL_LABEL_TO_SIZE,
)


class TestSelectDescriptions:
    """Tests for select descriptions."""

    def test_robot_select_count(self):
        assert len(ROBOT_SELECT_DESCRIPTIONS) == 3

    def test_feeder_select_count(self):
        assert len(FEEDER_SELECT_DESCRIPTIONS) == 1

    def test_night_light_mode_description(self):
        desc = ROBOT_SELECT_DESCRIPTIONS[0]
        assert desc.key == "night_light_mode"
        assert len(desc.options) > 0

    def test_wait_time_options(self):
        desc = ROBOT_SELECT_DESCRIPTIONS[2]  # wait_time
        assert "3" in desc.options
        assert "7" in desc.options
        assert "15" in desc.options
        assert "25" in desc.options
        assert "30" in desc.options


class TestNightLightIcon:
    """Tests for _night_light_icon."""

    def test_on(self):
        from pylitterbot.robot.litterrobot5 import NightLightMode
        assert _night_light_icon(NightLightMode.ON.value) == "mdi:lightbulb-on"

    def test_auto(self):
        from pylitterbot.robot.litterrobot5 import NightLightMode
        assert _night_light_icon(NightLightMode.AUTO.value) == "mdi:lightbulb-auto"

    def test_off(self):
        from pylitterbot.robot.litterrobot5 import NightLightMode
        assert _night_light_icon(NightLightMode.OFF.value) == "mdi:lightbulb-off"

    def test_none(self):
        assert _night_light_icon(None) == "mdi:lightbulb-off"


class TestLitterRobotSelect:
    """Tests for LitterRobotSelect entity."""

    def test_wait_time_current(self, mock_litter_robot, mock_hub):
        """Test wait time current option."""
        desc = ROBOT_SELECT_DESCRIPTIONS[2]  # wait_time
        select = LitterRobotSelect(mock_litter_robot, mock_hub, desc)
        assert select.current_option == "7"

    def test_wait_time_options(self, mock_litter_robot, mock_hub):
        """Test wait time options list."""
        desc = ROBOT_SELECT_DESCRIPTIONS[2]
        select = LitterRobotSelect(mock_litter_robot, mock_hub, desc)
        assert select.options == ["3", "7", "15", "25", "30"]

    async def test_select_option(self, mock_litter_robot, mock_hub):
        """Test selecting a wait time option."""
        desc = ROBOT_SELECT_DESCRIPTIONS[2]
        select = LitterRobotSelect(mock_litter_robot, mock_hub, desc)
        select.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await select.async_select_option("15")

        mock_litter_robot.set_wait_time.assert_awaited_once_with(15)

    def test_panel_brightness_icon(self, mock_litter_robot, mock_hub):
        """Test panel brightness uses static icon."""
        desc = ROBOT_SELECT_DESCRIPTIONS[1]  # panel_brightness
        select = LitterRobotSelect(mock_litter_robot, mock_hub, desc)
        assert select.icon == "mdi:brightness-6"

    def test_night_light_mode_icon(self, mock_litter_robot, mock_hub):
        """Test night light mode uses icon_fn."""
        desc = ROBOT_SELECT_DESCRIPTIONS[0]
        select = LitterRobotSelect(mock_litter_robot, mock_hub, desc)
        # current_option returns the night_light_mode.value = "AUTO"
        icon = select.icon
        assert icon is not None

    def test_meal_insert_size_current(self, mock_feeder_robot, mock_hub):
        """Test meal insert size current option."""
        desc = FEEDER_SELECT_DESCRIPTIONS[0]
        select = LitterRobotSelect(mock_feeder_robot, mock_hub, desc)
        assert select.current_option == "1/8 cup"

    async def test_meal_insert_size_select(self, mock_feeder_robot, mock_hub):
        """Test selecting meal insert size."""
        desc = FEEDER_SELECT_DESCRIPTIONS[0]
        select = LitterRobotSelect(mock_feeder_robot, mock_hub, desc)
        select.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await select.async_select_option("1/4 cup")

        mock_feeder_robot.set_meal_insert_size.assert_awaited_once_with(0.25)
