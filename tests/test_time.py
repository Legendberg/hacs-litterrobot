"""Tests for the Litter-Robot time platform."""
from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.time import (
    TIME_DESCRIPTIONS,
    LitterRobotSleepTimeEntity,
    _minutes_to_time,
    _time_to_minutes,
    _get_schedule_time,
    _patch_schedule_time,
    WEEKDAY_DAYS,
    WEEKEND_DAYS,
)


class TestTimeConversions:
    """Tests for time conversion functions."""

    def test_minutes_to_time_midnight(self):
        assert _minutes_to_time(0) == time(0, 0)

    def test_minutes_to_time_noon(self):
        assert _minutes_to_time(720) == time(12, 0)

    def test_minutes_to_time_1320(self):
        """1320 minutes = 22:00."""
        assert _minutes_to_time(1320) == time(22, 0)

    def test_minutes_to_time_420(self):
        """420 minutes = 07:00."""
        assert _minutes_to_time(420) == time(7, 0)

    def test_minutes_to_time_none(self):
        assert _minutes_to_time(None) is None

    def test_time_to_minutes_midnight(self):
        assert _time_to_minutes(time(0, 0)) == 0

    def test_time_to_minutes_noon(self):
        assert _time_to_minutes(time(12, 0)) == 720

    def test_time_to_minutes_2200(self):
        assert _time_to_minutes(time(22, 0)) == 1320

    def test_time_to_minutes_with_minutes(self):
        assert _time_to_minutes(time(7, 30)) == 450


class TestGetScheduleTime:
    """Tests for _get_schedule_time."""

    def test_get_weekday_sleep_time(self, mock_litter_robot):
        """Test getting weekday sleep time from schedule."""
        result = _get_schedule_time(mock_litter_robot, WEEKDAY_DAYS, "sleepTime")
        assert result == time(22, 0)

    def test_get_weekday_wake_time(self, mock_litter_robot):
        """Test getting weekday wake time from schedule."""
        result = _get_schedule_time(mock_litter_robot, WEEKDAY_DAYS, "wakeTime")
        assert result == time(7, 0)

    def test_get_weekend_sleep_time(self, mock_litter_robot):
        """Test getting weekend sleep time from schedule."""
        result = _get_schedule_time(mock_litter_robot, WEEKEND_DAYS, "sleepTime")
        assert result == time(23, 0)

    def test_get_weekend_wake_time(self, mock_litter_robot):
        """Test getting weekend wake time from schedule."""
        result = _get_schedule_time(mock_litter_robot, WEEKEND_DAYS, "wakeTime")
        assert result == time(8, 0)

    def test_empty_schedule(self, mock_litter_robot):
        """Test with empty schedule returns None."""
        mock_litter_robot._data = {"sleepSchedules": []}
        result = _get_schedule_time(mock_litter_robot, WEEKDAY_DAYS, "sleepTime")
        assert result is None


class TestPatchScheduleTime:
    """Tests for _patch_schedule_time."""

    async def test_patch_weekday_sleep(self, mock_litter_robot):
        """Test patching weekday sleep time."""
        await _patch_schedule_time(
            mock_litter_robot, WEEKDAY_DAYS, "sleepTime", time(23, 30)
        )

        mock_litter_robot._patch.assert_awaited_once()
        call_args = mock_litter_robot._patch.call_args
        schedules = call_args[1]["json"]["sleepSchedules"]

        for sched in schedules:
            if sched["dayOfWeek"] in WEEKDAY_DAYS:
                assert sched["sleepTime"] == 1410  # 23*60+30
            else:
                assert sched["sleepTime"] == 1380  # unchanged

    async def test_patch_empty_schedules(self, mock_litter_robot):
        """Test patching creates default schedules if empty."""
        mock_litter_robot._data = {"sleepSchedules": []}

        await _patch_schedule_time(
            mock_litter_robot, WEEKEND_DAYS, "wakeTime", time(9, 0)
        )

        mock_litter_robot._patch.assert_awaited_once()
        call_args = mock_litter_robot._patch.call_args
        schedules = call_args[1]["json"]["sleepSchedules"]
        assert len(schedules) == 7

        for sched in schedules:
            if sched["dayOfWeek"] in WEEKEND_DAYS:
                assert sched["wakeTime"] == 540  # 9*60


class TestTimeDescriptions:
    """Tests for time descriptions."""

    def test_descriptions_count(self):
        assert len(TIME_DESCRIPTIONS) == 4

    def test_sleep_start_weekday(self):
        desc = TIME_DESCRIPTIONS[0]
        assert desc.key == "sleep_start_weekday"
        assert desc.days == WEEKDAY_DAYS
        assert desc.schedule_field == "sleepTime"
        assert desc.icon == "mdi:weather-night"

    def test_sleep_end_weekend(self):
        desc = TIME_DESCRIPTIONS[3]
        assert desc.key == "sleep_end_weekend"
        assert desc.days == WEEKEND_DAYS
        assert desc.schedule_field == "wakeTime"
        assert desc.icon == "mdi:weather-sunny"


class TestSleepTimeEntity:
    """Tests for LitterRobotSleepTimeEntity."""

    def test_native_value(self, mock_litter_robot, mock_hub):
        """Test time entity returns correct time value."""
        desc = TIME_DESCRIPTIONS[0]  # sleep_start_weekday
        entity = LitterRobotSleepTimeEntity(mock_litter_robot, mock_hub, desc)
        assert entity.native_value == time(22, 0)

    async def test_set_value(self, mock_litter_robot, mock_hub):
        """Test setting the time value."""
        desc = TIME_DESCRIPTIONS[0]
        entity = LitterRobotSleepTimeEntity(mock_litter_robot, mock_hub, desc)
        entity.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await entity.async_set_value(time(23, 0))

        mock_litter_robot._patch.assert_awaited_once()
