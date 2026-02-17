"""Tests for the Litter-Robot base entity classes."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.entity import (
    LitterRobotEntity,
    LitterRobotControlEntity,
    is_litter_robot,
    is_feeder_robot,
    is_lr5,
    is_lr5_pro,
    REFRESH_WAIT_TIME_SECONDS,
)
from custom_components.litterrobot.const import DOMAIN


# --- Filter function tests ---


def test_is_litter_robot():
    """Test is_litter_robot with actual isinstance check."""
    from pylitterbot import LitterRobot
    from pylitterbot.robot.litterrobot5 import LitterRobot5

    lr_mock = MagicMock(spec=LitterRobot)
    lr5_mock = MagicMock(spec=LitterRobot5)
    other_mock = MagicMock()

    assert is_litter_robot(lr_mock) is True
    assert is_litter_robot(lr5_mock) is True
    assert is_litter_robot(other_mock) is False


def test_is_feeder_robot():
    """Test is_feeder_robot with actual isinstance check."""
    from pylitterbot.robot.feederrobot import FeederRobot

    feeder_mock = MagicMock(spec=FeederRobot)
    other_mock = MagicMock()

    assert is_feeder_robot(feeder_mock) is True
    assert is_feeder_robot(other_mock) is False


def test_is_lr5():
    """Test is_lr5 with actual isinstance check."""
    from pylitterbot.robot.litterrobot5 import LitterRobot5

    lr5_mock = MagicMock(spec=LitterRobot5)
    other_mock = MagicMock()

    assert is_lr5(lr5_mock) is True
    assert is_lr5(other_mock) is False


def test_is_lr5_pro():
    """Test is_lr5_pro checks both isinstance and is_pro."""
    from pylitterbot.robot.litterrobot5 import LitterRobot5

    lr5_pro = MagicMock(spec=LitterRobot5)
    lr5_pro.is_pro = True
    lr5_not_pro = MagicMock(spec=LitterRobot5)
    lr5_not_pro.is_pro = False
    other = MagicMock()

    assert is_lr5_pro(lr5_pro) is True
    assert is_lr5_pro(lr5_not_pro) is False
    assert is_lr5_pro(other) is False


# --- Entity tests ---


def test_entity_unique_id(mock_litter_robot, mock_hub):
    """Test entity unique_id format."""
    entity = LitterRobotEntity(mock_litter_robot, "Waste Drawer", mock_hub)
    assert entity.unique_id == "LR5-TEST-SERIAL-Waste Drawer"


def test_entity_name(mock_litter_robot, mock_hub):
    """Test entity name format."""
    entity = LitterRobotEntity(mock_litter_robot, "Waste Drawer", mock_hub)
    assert entity.name == "Test Robot Waste Drawer"


def test_entity_device_info(mock_litter_robot, mock_hub):
    """Test entity device info."""
    entity = LitterRobotEntity(mock_litter_robot, "Waste Drawer", mock_hub)
    info = entity.device_info
    assert info["identifiers"] == {(DOMAIN, "LR5-TEST-SERIAL")}
    assert info["name"] == "Test Robot"
    assert info["manufacturer"] == "Litter-Robot"
    assert info["model"] == "Litter-Robot 5"


def test_control_entity_cancel_refresh(mock_litter_robot, mock_hub):
    """Test control entity cancels refresh callback."""
    entity = LitterRobotControlEntity(mock_litter_robot, "Test", mock_hub)
    assert entity._refresh_callback is None

    # Set a mock callback
    cancel_fn = MagicMock()
    entity._refresh_callback = cancel_fn

    entity.async_cancel_refresh_callback()
    cancel_fn.assert_called_once()
    assert entity._refresh_callback is None


async def test_control_entity_perform_action(mock_litter_robot, mock_hub):
    """Test perform_action_and_refresh calls action and schedules refresh."""
    entity = LitterRobotControlEntity(mock_litter_robot, "Test", mock_hub)
    entity.hass = MagicMock()

    action = AsyncMock()
    with patch(
        "custom_components.litterrobot.entity.async_call_later"
    ) as mock_call_later:
        mock_call_later.return_value = MagicMock()
        result = await entity.perform_action_and_refresh(action, "arg1")

    assert result is True
    action.assert_awaited_once_with("arg1")
    mock_call_later.assert_called_once()
