"""Tests for the Litter-Robot vacuum platform.

Note: The vacuum module uses VacuumActivity which may not be available in older
HA versions. These tests mock the vacuum module imports to be compatible.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import sys

import pytest


# VacuumActivity was added in HA 2024.8+. Create a compatibility shim
# so we can test without it being present.
try:
    from homeassistant.components.vacuum import VacuumActivity
except ImportError:
    # Create a mock VacuumActivity enum for testing
    class VacuumActivity:
        CLEANING = "cleaning"
        DOCKED = "docked"
        ERROR = "error"
        PAUSED = "paused"
        IDLE = "idle"
        RETURNING = "returning"

    # Patch it into the homeassistant.components.vacuum module
    import homeassistant.components.vacuum as vacuum_mod
    vacuum_mod.VacuumActivity = VacuumActivity

# Now we can safely import our module
from custom_components.litterrobot.vacuum import (
    LitterRobotCleaner,
    TYPE_LITTER_BOX,
    SUPPORT_LITTERROBOT,
)


@pytest.fixture
def vacuum(mock_litter_robot, mock_hub):
    """Return a LitterRobotCleaner instance."""
    return LitterRobotCleaner(
        robot=mock_litter_robot, entity_type=TYPE_LITTER_BOX, hub=mock_hub
    )


class TestVacuumActivity:
    """Tests for vacuum activity mapping."""

    def test_ready_is_docked(self, vacuum, mock_litter_robot):
        """Test READY status maps to DOCKED."""
        from pylitterbot.enums import LitterBoxStatus

        mock_litter_robot.status = LitterBoxStatus.READY
        assert vacuum.activity == VacuumActivity.DOCKED

    def test_clean_cycle_is_cleaning(self, vacuum, mock_litter_robot):
        """Test CLEAN_CYCLE maps to CLEANING."""
        from pylitterbot.enums import LitterBoxStatus

        mock_litter_robot.status = LitterBoxStatus.CLEAN_CYCLE
        assert vacuum.activity == VacuumActivity.CLEANING

    def test_empty_cycle_is_cleaning(self, vacuum, mock_litter_robot):
        """Test EMPTY_CYCLE maps to CLEANING."""
        from pylitterbot.enums import LitterBoxStatus

        mock_litter_robot.status = LitterBoxStatus.EMPTY_CYCLE
        assert vacuum.activity == VacuumActivity.CLEANING

    def test_cat_sensor_interrupted_is_paused(self, vacuum, mock_litter_robot):
        """Test CAT_SENSOR_INTERRUPTED maps to PAUSED."""
        from pylitterbot.enums import LitterBoxStatus

        mock_litter_robot.status = LitterBoxStatus.CAT_SENSOR_INTERRUPTED
        assert vacuum.activity == VacuumActivity.PAUSED

    def test_unknown_status_is_error(self, vacuum, mock_litter_robot):
        """Test unknown status maps to ERROR."""
        mock_litter_robot.status = MagicMock()
        # Any status not in the switcher should return ERROR
        assert vacuum.activity == VacuumActivity.ERROR

    def test_off_is_docked(self, vacuum, mock_litter_robot):
        """Test OFF status maps to DOCKED."""
        from pylitterbot.enums import LitterBoxStatus

        mock_litter_robot.status = LitterBoxStatus.OFF
        assert vacuum.activity == VacuumActivity.DOCKED


class TestVacuumStatus:
    """Tests for vacuum status string."""

    def test_status_text(self, vacuum, mock_litter_robot):
        """Test status returns text."""
        mock_litter_robot.is_sleeping = False
        status_mock = MagicMock()
        status_mock.text = "Ready"
        mock_litter_robot.status = status_mock
        assert vacuum.status == "Ready"

    def test_status_sleeping(self, vacuum, mock_litter_robot):
        """Test status appends (Sleeping) when sleeping."""
        mock_litter_robot.is_sleeping = True
        status_mock = MagicMock()
        status_mock.text = "Ready"
        mock_litter_robot.status = status_mock
        assert vacuum.status == "Ready (Sleeping)"


class TestVacuumActions:
    """Tests for vacuum actions."""

    async def test_start(self, vacuum, mock_litter_robot):
        """Test start cleaning."""
        vacuum.hass = MagicMock()
        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await vacuum.async_start()
        mock_litter_robot.start_cleaning.assert_awaited_once()

    async def test_turn_on(self, vacuum, mock_litter_robot):
        """Test turn on."""
        vacuum.hass = MagicMock()
        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await vacuum.async_turn_on()
        mock_litter_robot.set_power_status.assert_awaited_once_with(True)

    async def test_turn_off(self, vacuum, mock_litter_robot):
        """Test turn off."""
        vacuum.hass = MagicMock()
        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await vacuum.async_turn_off()
        mock_litter_robot.set_power_status.assert_awaited_once_with(False)

    async def test_reset_waste_drawer(self, vacuum, mock_litter_robot, mock_hub):
        """Test reset waste drawer."""
        await vacuum.async_reset_waste_drawer()
        mock_litter_robot.reset_waste_drawer.assert_awaited_once()
        mock_hub.coordinator.async_set_updated_data.assert_called_once_with(True)

    async def test_set_wait_time(self, vacuum, mock_litter_robot):
        """Test set wait time."""
        vacuum.hass = MagicMock()
        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await vacuum.async_set_wait_time(15)
        mock_litter_robot.set_wait_time.assert_awaited_once_with(15)


class TestVacuumAttributes:
    """Tests for vacuum extra state attributes."""

    def test_extra_state_attributes(self, vacuum, mock_litter_robot):
        """Test extra state attributes contain expected keys."""
        attrs = vacuum.extra_state_attributes
        assert "clean_cycle_wait_time_minutes" in attrs
        assert "is_sleeping" in attrs
        assert "sleep_mode_enabled" in attrs
        assert "power_status" in attrs
        assert "status_code" in attrs
        assert "last_seen" in attrs
        assert attrs["clean_cycle_wait_time_minutes"] == 7

    def test_supported_features(self, vacuum):
        """Test supported features."""
        assert vacuum.supported_features == SUPPORT_LITTERROBOT
