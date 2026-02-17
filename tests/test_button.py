"""Tests for the Litter-Robot button platform."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.button import (
    ROBOT_BUTTON_DESCRIPTIONS,
    FEEDER_BUTTON_DESCRIPTIONS,
    LitterRobotButton,
)


class TestButtonDescriptions:
    """Tests for button descriptions."""

    def test_robot_button_count(self):
        assert len(ROBOT_BUTTON_DESCRIPTIONS) == 4

    def test_feeder_button_count(self):
        assert len(FEEDER_BUTTON_DESCRIPTIONS) == 1

    def test_clean_cycle_description(self):
        desc = ROBOT_BUTTON_DESCRIPTIONS[0]
        assert desc.key == "clean_cycle"
        assert desc.entity_type == "Clean Cycle"
        assert desc.icon == "mdi:play-circle"

    def test_give_snack_description(self):
        desc = FEEDER_BUTTON_DESCRIPTIONS[0]
        assert desc.key == "give_snack"
        assert desc.entity_type == "Give Snack"


class TestLitterRobotButton:
    """Tests for LitterRobotButton entity."""

    async def test_clean_cycle_press(self, mock_litter_robot, mock_hub):
        """Test clean cycle button calls start_cleaning."""
        desc = ROBOT_BUTTON_DESCRIPTIONS[0]  # clean_cycle
        button = LitterRobotButton(mock_litter_robot, mock_hub, desc)
        button.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await button.async_press()

        mock_litter_robot.start_cleaning.assert_awaited_once()

    async def test_reset_waste_drawer_press(self, mock_litter_robot, mock_hub):
        """Test reset waste drawer button uses coordinator update."""
        desc = ROBOT_BUTTON_DESCRIPTIONS[1]  # reset_waste_drawer
        button = LitterRobotButton(mock_litter_robot, mock_hub, desc)

        await button.async_press()

        mock_litter_robot.reset_waste_drawer.assert_awaited_once()
        mock_hub.coordinator.async_set_updated_data.assert_called_once_with(True)

    async def test_recalibrate_press(self, mock_litter_robot, mock_hub):
        """Test recalibrate button calls reset."""
        desc = ROBOT_BUTTON_DESCRIPTIONS[2]  # recalibrate
        button = LitterRobotButton(mock_litter_robot, mock_hub, desc)
        button.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await button.async_press()

        mock_litter_robot.reset.assert_awaited_once()

    async def test_change_filter_press(self, mock_litter_robot, mock_hub):
        """Test change filter button uses coordinator update."""
        desc = ROBOT_BUTTON_DESCRIPTIONS[3]  # change_filter
        button = LitterRobotButton(mock_litter_robot, mock_hub, desc)

        await button.async_press()

        mock_litter_robot.change_filter.assert_awaited_once()
        mock_hub.coordinator.async_set_updated_data.assert_called()

    async def test_give_snack_press(self, mock_feeder_robot, mock_hub):
        """Test give snack button calls give_snack."""
        desc = FEEDER_BUTTON_DESCRIPTIONS[0]  # give_snack
        button = LitterRobotButton(mock_feeder_robot, mock_hub, desc)
        button.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await button.async_press()

        mock_feeder_robot.give_snack.assert_awaited_once()
