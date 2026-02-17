"""Tests for the Litter-Robot switch platform."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.switch import (
    ROBOT_SWITCH_DESCRIPTIONS,
    FEEDER_SWITCH_DESCRIPTIONS,
    LitterRobotSwitch,
    LitterRobotSleepModeSwitch,
    WEEKDAY_DAYS,
    WEEKEND_DAYS,
)


class TestSwitchDescriptions:
    """Tests for switch descriptions."""

    def test_robot_switch_count(self):
        assert len(ROBOT_SWITCH_DESCRIPTIONS) == 2

    def test_feeder_switch_count(self):
        assert len(FEEDER_SWITCH_DESCRIPTIONS) == 3

    def test_night_light_description(self):
        desc = ROBOT_SWITCH_DESCRIPTIONS[0]
        assert desc.key == "night_light_mode"
        assert desc.entity_type == "Night Light Mode"

    def test_panel_lockout_description(self):
        desc = ROBOT_SWITCH_DESCRIPTIONS[1]
        assert desc.key == "panel_lockout"
        assert desc.entity_type == "Panel Lockout"


class TestLitterRobotSwitch:
    """Tests for LitterRobotSwitch entity."""

    def test_panel_lockout_is_off(self, mock_litter_robot, mock_hub):
        """Test panel lockout switch is off."""
        desc = ROBOT_SWITCH_DESCRIPTIONS[1]  # panel_lockout
        switch = LitterRobotSwitch(mock_litter_robot, mock_hub, desc)
        assert switch.is_on is False
        assert switch.icon == "mdi:lock-open"

    def test_panel_lockout_is_on(self, mock_litter_robot, mock_hub):
        """Test panel lockout switch is on."""
        mock_litter_robot.panel_lock_enabled = True
        desc = ROBOT_SWITCH_DESCRIPTIONS[1]
        switch = LitterRobotSwitch(mock_litter_robot, mock_hub, desc)
        assert switch.is_on is True
        assert switch.icon == "mdi:lock"

    async def test_turn_on(self, mock_litter_robot, mock_hub):
        """Test turning on a switch."""
        desc = ROBOT_SWITCH_DESCRIPTIONS[1]  # panel_lockout
        switch = LitterRobotSwitch(mock_litter_robot, mock_hub, desc)
        switch.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await switch.async_turn_on()

        mock_litter_robot.set_panel_lockout.assert_awaited_once_with(True)

    async def test_turn_off(self, mock_litter_robot, mock_hub):
        """Test turning off a switch."""
        desc = ROBOT_SWITCH_DESCRIPTIONS[1]
        switch = LitterRobotSwitch(mock_litter_robot, mock_hub, desc)
        switch.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await switch.async_turn_off()

        mock_litter_robot.set_panel_lockout.assert_awaited_once_with(False)

    def test_gravity_mode_switch(self, mock_feeder_robot, mock_hub):
        """Test gravity mode switch state."""
        desc = FEEDER_SWITCH_DESCRIPTIONS[2]  # gravity_mode
        switch = LitterRobotSwitch(mock_feeder_robot, mock_hub, desc)
        assert switch.is_on is False
        assert switch.icon == "mdi:arrow-down-bold-outline"

    def test_static_icon_switch(self, mock_litter_robot, mock_hub):
        """Test switch with no icon_fn uses static icon."""
        desc = MagicMock()
        desc.entity_type = "Test"
        desc.is_on_fn = lambda r: True
        desc.icon_fn = None
        desc.icon = "mdi:test"
        switch = LitterRobotSwitch(mock_litter_robot, mock_hub, desc)
        assert switch.icon == "mdi:test"


class TestSleepModeSwitch:
    """Tests for LitterRobotSleepModeSwitch."""

    def test_weekday_sleep_on(self, mock_litter_robot, mock_hub):
        """Test weekday sleep mode is on when all weekdays enabled."""
        switch = LitterRobotSleepModeSwitch(
            mock_litter_robot, "Sleep Mode Weekday", mock_hub, WEEKDAY_DAYS
        )
        assert switch.is_on is True
        assert switch.icon == "mdi:sleep"

    def test_weekend_sleep_off(self, mock_litter_robot, mock_hub):
        """Test weekend sleep mode is off when weekend days disabled."""
        switch = LitterRobotSleepModeSwitch(
            mock_litter_robot, "Sleep Mode Weekend", mock_hub, WEEKEND_DAYS
        )
        assert switch.is_on is False
        assert switch.icon == "mdi:sleep-off"

    async def test_turn_on_sleep(self, mock_litter_robot, mock_hub):
        """Test turning on sleep mode patches schedule."""
        switch = LitterRobotSleepModeSwitch(
            mock_litter_robot, "Sleep Mode Weekend", mock_hub, WEEKEND_DAYS
        )
        switch.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await switch.async_turn_on()

        mock_litter_robot._patch.assert_awaited_once()
        call_args = mock_litter_robot._patch.call_args
        schedules = call_args[1]["json"]["sleepSchedules"]
        for sched in schedules:
            if sched["dayOfWeek"] in WEEKEND_DAYS:
                assert sched["isEnabled"] is True

    async def test_turn_off_sleep(self, mock_litter_robot, mock_hub):
        """Test turning off sleep mode patches schedule."""
        switch = LitterRobotSleepModeSwitch(
            mock_litter_robot, "Sleep Mode Weekday", mock_hub, WEEKDAY_DAYS
        )
        switch.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await switch.async_turn_off()

        mock_litter_robot._patch.assert_awaited_once()
        call_args = mock_litter_robot._patch.call_args
        schedules = call_args[1]["json"]["sleepSchedules"]
        for sched in schedules:
            if sched["dayOfWeek"] in WEEKDAY_DAYS:
                assert sched["isEnabled"] is False

    def test_empty_schedules(self, mock_litter_robot, mock_hub):
        """Test sleep mode with empty schedules returns False."""
        mock_litter_robot._data = {"sleepSchedules": []}
        switch = LitterRobotSleepModeSwitch(
            mock_litter_robot, "Sleep Mode Weekday", mock_hub, WEEKDAY_DAYS
        )
        assert switch.is_on is True  # all() on empty iterable is True
