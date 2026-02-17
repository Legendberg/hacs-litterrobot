"""Tests for the Litter-Robot hub."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.hub import EVENT_LITTERROBOT, LitterRobotHub


@pytest.fixture
def hub_instance():
    """Create a real LitterRobotHub for testing event logic."""
    hass = MagicMock()
    hass.bus.async_fire = MagicMock()
    hass.async_create_task = MagicMock()
    data = {"username": "test@example.com", "password": "test_password"}

    with patch(
        "custom_components.litterrobot.hub.DataUpdateCoordinator"
    ):
        hub = LitterRobotHub(hass, data)

    return hub


@pytest.fixture
def hub_with_options():
    """Create a LitterRobotHub with a mock config entry and options."""
    hass = MagicMock()
    hass.bus.async_fire = MagicMock()
    hass.async_create_task = MagicMock()
    hass.services.async_call = AsyncMock()

    entry = MagicMock()
    entry.data = {"username": "test@example.com", "password": "test_password"}
    entry.options = {
        "notify_service": "mobile_app_legendberg",
        "notify_events": [
            "clean_cycle_complete",
            "cat_sensor_interrupted",
            "waste_drawer_full",
            "pet_visit",
            "robot_online",
            "robot_offline",
            "drawer_removed",
            "bonnet_removed",
            "pinch_detected",
            "motor_fault",
        ],
        "notify_warning": [
            "cat_sensor_interrupted",
            "robot_offline",
            "drawer_removed",
            "bonnet_removed",
        ],
        "notify_critical": [
            "waste_drawer_full",
            "pinch_detected",
            "motor_fault",
        ],
    }

    with patch(
        "custom_components.litterrobot.hub.DataUpdateCoordinator"
    ):
        hub = LitterRobotHub(hass, entry)

    return hub


def _make_robot(serial="LR5-TEST", name="Test Robot", status=None,
                is_online=True, waste_drawer_level=50,
                is_drawer_removed=False, is_bonnet_removed=False,
                pinch_status="NONE", motor_fault_status="NONE"):
    """Helper to create a mock robot."""
    robot = MagicMock()
    robot.serial = serial
    robot.name = name
    robot.status = status
    robot.is_online = is_online
    robot.waste_drawer_level = waste_drawer_level
    robot.is_drawer_removed = is_drawer_removed
    robot.is_bonnet_removed = is_bonnet_removed
    pinch_mock = MagicMock()
    pinch_mock.__str__ = lambda self: pinch_status
    robot.pinch_status = pinch_mock
    motor_mock = MagicMock()
    motor_mock.__str__ = lambda self: motor_fault_status
    robot.globe_motor_fault_status = motor_mock
    return robot


def _make_pet(pet_id="pet-1", name="Test Cat", weight_history_count=5):
    """Helper to create a mock pet."""
    pet = MagicMock()
    pet.id = pet_id
    pet.name = name
    entries = []
    for i in range(weight_history_count):
        entry = MagicMock()
        entry.weight = 10.0 + i * 0.1
        entries.append(entry)
    pet.weight_history = entries
    return pet


async def test_login_success(hub_instance):
    """Test successful login."""
    with patch("custom_components.litterrobot.hub.Account") as mock_acct_cls:
        mock_account = MagicMock()
        mock_account.connect = AsyncMock()
        mock_account.load_pets = AsyncMock()
        mock_acct_cls.return_value = mock_account

        await hub_instance.login(load_robots=True)

    assert hub_instance.logged_in is True
    assert hub_instance.account is mock_account
    mock_account.connect.assert_awaited_once()
    mock_account.load_pets.assert_awaited_once()


async def test_login_failure(hub_instance):
    """Test login failure raises exception."""
    from pylitterbot.exceptions import LitterRobotLoginException

    with patch("custom_components.litterrobot.hub.Account") as mock_acct_cls:
        mock_account = MagicMock()
        mock_account.connect = AsyncMock(side_effect=LitterRobotLoginException)
        mock_acct_cls.return_value = mock_account

        with pytest.raises(LitterRobotLoginException):
            await hub_instance.login()

    assert hub_instance.logged_in is False


def test_no_event_on_first_check(hub_instance):
    """Test no events fire on first state check (no previous state)."""
    robot = _make_robot()
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_not_called()


def test_clean_cycle_complete_event(hub_instance):
    """Test clean cycle complete event fires on status transition."""
    from pylitterbot.enums import LitterBoxStatus

    robot = _make_robot(status=LitterBoxStatus.CLEAN_CYCLE)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    # First check: establish baseline
    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    # Transition to READY
    robot.status = LitterBoxStatus.READY
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][0] == EVENT_LITTERROBOT
    assert call_args[0][1]["type"] == "clean_cycle_complete"
    assert call_args[0][1]["device_id"] == "LR5-TEST"


def test_cat_sensor_interrupted_event(hub_instance):
    """Test cat sensor interrupted event fires when cat interrupts a clean cycle."""
    from pylitterbot.enums import LitterBoxStatus

    robot = _make_robot(status=LitterBoxStatus.CLEAN_CYCLE)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    # First check: establish baseline
    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    # Cat jumps in during cycle
    robot.status = LitterBoxStatus.CAT_SENSOR_INTERRUPTED
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][0] == EVENT_LITTERROBOT
    assert call_args[0][1]["type"] == "cat_sensor_interrupted"
    assert call_args[0][1]["device_id"] == "LR5-TEST"


def test_waste_drawer_full_event(hub_instance):
    """Test waste drawer full event fires when level reaches 100."""
    robot = _make_robot(waste_drawer_level=90)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    # First check: baseline at 90%
    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    # Level goes to 100
    robot.waste_drawer_level = 100
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "waste_drawer_full"
    assert call_args[0][1]["level"] == 100


def test_robot_offline_event(hub_instance):
    """Test robot offline event fires when is_online changes to False."""
    robot = _make_robot(is_online=True)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    robot.is_online = False
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "robot_offline"


def test_robot_online_event(hub_instance):
    """Test robot online event fires when is_online changes to True."""
    robot = _make_robot(is_online=False)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    robot.is_online = True
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "robot_online"


def test_pet_visit_event(hub_instance):
    """Test pet visit event fires when weight history count increases."""
    pet = _make_pet(weight_history_count=5)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = []
    hub_instance.account.pets = [pet]

    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    # Add a new weight history entry (count goes from 5 to 6)
    new_entry = MagicMock()
    new_entry.weight = 10.55
    pet.weight_history = [new_entry] + pet.weight_history

    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "pet_visit"
    assert call_args[0][1]["pet_name"] == "Test Cat"
    assert call_args[0][1]["weight"] == 10.55


def test_no_duplicate_events(hub_instance):
    """Test that same state doesn't fire duplicate events."""
    robot = _make_robot(waste_drawer_level=100)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    # First check: baseline (waste already at 100, no previous, no event)
    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    # Second check: still at 100, no event (already was at 100)
    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()


def test_drawer_removed_event(hub_instance):
    """Test drawer removed event fires when is_drawer_removed changes to True."""
    robot = _make_robot(is_drawer_removed=False)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    robot.is_drawer_removed = True
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "drawer_removed"


def test_bonnet_removed_event(hub_instance):
    """Test bonnet removed event fires when is_bonnet_removed changes to True."""
    robot = _make_robot(is_bonnet_removed=False)
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    robot.is_bonnet_removed = True
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "bonnet_removed"


def test_pinch_detected_event(hub_instance):
    """Test pinch detected event fires when pinch_status changes from NONE."""
    robot = _make_robot(pinch_status="NONE")
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    # Change pinch status to a fault
    pinch_mock = MagicMock()
    pinch_mock.__str__ = lambda self: "DETECTED"
    robot.pinch_status = pinch_mock
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "pinch_detected"
    assert call_args[0][1]["status"] == "DETECTED"


def test_motor_fault_event(hub_instance):
    """Test motor fault event fires when motor fault status changes from NONE."""
    robot = _make_robot(motor_fault_status="NONE")
    hub_instance.account = MagicMock()
    hub_instance.account.robots = [robot]
    hub_instance.account.pets = []

    hub_instance._check_and_fire_events()
    hub_instance.hass.bus.async_fire.assert_not_called()

    # Change motor fault status
    motor_mock = MagicMock()
    motor_mock.__str__ = lambda self: "FAULT"
    robot.globe_motor_fault_status = motor_mock
    hub_instance._check_and_fire_events()

    hub_instance.hass.bus.async_fire.assert_called_once()
    call_args = hub_instance.hass.bus.async_fire.call_args
    assert call_args[0][1]["type"] == "motor_fault"
    assert call_args[0][1]["status"] == "FAULT"


def test_hub_accepts_config_entry(hub_with_options):
    """Test hub accepts a ConfigEntry and stores entry reference."""
    assert hub_with_options._entry is not None
    assert hub_with_options._data == {
        "username": "test@example.com",
        "password": "test_password",
    }


def test_hub_accepts_plain_dict(hub_instance):
    """Test hub accepts a plain dict and sets entry to None."""
    assert hub_instance._entry is None
    assert hub_instance._data == {
        "username": "test@example.com",
        "password": "test_password",
    }


async def test_notification_sent(hub_with_options):
    """Test notification is sent when configured."""
    from pylitterbot.enums import LitterBoxStatus

    robot = _make_robot(status=LitterBoxStatus.CLEAN_CYCLE)
    hub_with_options.account = MagicMock()
    hub_with_options.account.robots = [robot]
    hub_with_options.account.pets = []

    # Establish baseline
    hub_with_options._check_and_fire_events()

    # Transition to READY
    robot.status = LitterBoxStatus.READY
    hub_with_options._check_and_fire_events()

    # async_create_task was called with the notification coroutine
    hub_with_options.hass.async_create_task.assert_called()

    # Execute the notification coroutine
    await hub_with_options._send_notification(
        "clean_cycle_complete",
        "Litter-Robot: Clean Cycle Complete",
        "Test Robot finished a clean cycle.",
    )

    hub_with_options.hass.services.async_call.assert_awaited_once_with(
        "notify",
        "mobile_app_legendberg",
        {
            "title": "Litter-Robot: Clean Cycle Complete",
            "message": "Test Robot finished a clean cycle.",
            "data": {
                "tag": "litterrobot_clean_cycle_complete",
                "group": "litter-robot",
            },
        },
    )


async def test_notification_disabled(hub_instance):
    """Test no notification sent when no entry (plain dict)."""
    await hub_instance._send_notification(
        "clean_cycle_complete",
        "Litter-Robot: Clean Cycle Complete",
        "Test Robot finished a clean cycle.",
    )
    # No service call since _entry is None
    hub_instance.hass.services.async_call.assert_not_called()


async def test_notification_no_service(hub_with_options):
    """Test no notification sent when service is empty."""
    hub_with_options._entry.options = {
        "notify_service": "",
        "notify_events": ["clean_cycle_complete"],
        "notify_critical": [],
    }
    await hub_with_options._send_notification(
        "clean_cycle_complete",
        "Litter-Robot: Clean Cycle Complete",
        "Test Robot finished a clean cycle.",
    )
    hub_with_options.hass.services.async_call.assert_not_awaited()


async def test_notification_event_not_enabled(hub_with_options):
    """Test no notification sent when event type is not in enabled list."""
    hub_with_options._entry.options = {
        "notify_service": "mobile_app_legendberg",
        "notify_events": ["waste_drawer_full"],  # clean_cycle_complete not included
        "notify_critical": [],
    }
    await hub_with_options._send_notification(
        "clean_cycle_complete",
        "Litter-Robot: Clean Cycle Complete",
        "Test Robot finished a clean cycle.",
    )
    hub_with_options.hass.services.async_call.assert_not_awaited()


async def test_notification_critical_data(hub_with_options):
    """Test critical events include critical push sound data."""
    await hub_with_options._send_notification(
        "pinch_detected",
        "Litter-Robot: Pinch Detected",
        "Test Robot detected a pinch.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert data["push"] == {"sound": {"name": "default", "critical": 1, "volume": 1.0}}


async def test_notification_warning_data(hub_with_options):
    """Test warning events include time-sensitive push data."""
    await hub_with_options._send_notification(
        "robot_offline",
        "Litter-Robot: Robot Offline",
        "Test Robot went OFFLINE.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert data["push"] == {"sound": "default", "interruption-level": "time-sensitive"}


async def test_notification_waste_drawer_full_critical(hub_with_options):
    """Test waste_drawer_full is a critical notification by default."""
    await hub_with_options._send_notification(
        "waste_drawer_full",
        "Litter-Robot: Waste Drawer Full",
        "Test Robot waste drawer is FULL.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert data["push"] == {"sound": {"name": "default", "critical": 1, "volume": 1.0}}


async def test_notification_normal_no_critical_data(hub_with_options):
    """Test non-critical events don't include push sound data."""
    await hub_with_options._send_notification(
        "clean_cycle_complete",
        "Litter-Robot: Clean Cycle Complete",
        "Test Robot finished a clean cycle.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert "push" not in data


async def test_notification_error_handling(hub_with_options):
    """Test notification failure is logged, not raised."""
    hub_with_options.hass.services.async_call = AsyncMock(
        side_effect=Exception("Service not found")
    )
    # Should not raise
    await hub_with_options._send_notification(
        "clean_cycle_complete",
        "Litter-Robot: Clean Cycle Complete",
        "Test Robot finished a clean cycle.",
    )


async def test_notification_drawer_removed_warning(hub_with_options):
    """Test drawer_removed is a warning notification by default."""
    await hub_with_options._send_notification(
        "drawer_removed",
        "Litter-Robot: Drawer Removed",
        "Test Robot waste drawer has been removed.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert "push" in data
    assert data["push"]["interruption-level"] == "time-sensitive"


async def test_notification_bonnet_removed_warning(hub_with_options):
    """Test bonnet_removed is a warning notification by default."""
    await hub_with_options._send_notification(
        "bonnet_removed",
        "Litter-Robot: Bonnet Removed",
        "Test Robot bonnet has been removed.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert "push" in data
    assert data["push"]["interruption-level"] == "time-sensitive"


async def test_notification_cat_sensor_interrupted_warning(hub_with_options):
    """Test cat_sensor_interrupted is a warning notification by default."""
    await hub_with_options._send_notification(
        "cat_sensor_interrupted",
        "Litter-Robot: Cat Interrupted Cycle",
        "Test Robot cycle was interrupted by cat sensor.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert "push" in data
    assert data["push"]["interruption-level"] == "time-sensitive"


async def test_notification_robot_offline_warning(hub_with_options):
    """Test robot_offline is a warning notification by default."""
    await hub_with_options._send_notification(
        "robot_offline",
        "Litter-Robot: Robot Offline",
        "Test Robot went OFFLINE.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert "push" in data
    assert data["push"]["interruption-level"] == "time-sensitive"


async def test_notification_pinch_critical(hub_with_options):
    """Test pinch_detected is a critical notification by default."""
    await hub_with_options._send_notification(
        "pinch_detected",
        "Litter-Robot: Pinch Detected",
        "Test Robot detected a pinch.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert "push" in data
    assert data["push"]["sound"]["critical"] == 1


async def test_notification_motor_fault_critical(hub_with_options):
    """Test motor_fault is a critical notification by default."""
    await hub_with_options._send_notification(
        "motor_fault",
        "Litter-Robot: Motor Fault",
        "Test Robot has a motor fault.",
    )
    call_args = hub_with_options.hass.services.async_call.call_args
    data = call_args[0][2]["data"]
    assert "push" in data
    assert data["push"]["sound"]["critical"] == 1
