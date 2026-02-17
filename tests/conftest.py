"""Shared fixtures for Litter-Robot tests."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "test_password"
DOMAIN = "litterrobot"


@pytest.fixture
def mock_litter_robot():
    """Return a mock LitterRobot5 with all attributes."""
    robot = MagicMock()
    robot.serial = "LR5-TEST-SERIAL"
    robot.name = "Test Robot"
    robot.model = "Litter-Robot 5"
    robot.is_pro = True

    # Sensor attributes
    robot.waste_drawer_level = 50
    robot.litter_level = 80
    robot.cycle_count = 1234
    robot.pet_weight = 10.5
    robot.wifi_rssi = -45
    robot.sound_volume = 75
    robot.firmware = "1.2.3.4"
    robot.scoops_saved_count = 500
    robot.next_filter_replacement_date = datetime(
        2026, 6, 1, tzinfo=timezone.utc
    )
    robot.setup_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    robot.last_seen = datetime(2026, 2, 16, 12, 0, 0, tzinfo=timezone.utc)
    robot.odometer_empty_cycles = 100
    robot.odometer_filter_cycles = 50
    robot.odometer_power_cycles = 10
    robot.last_reset_odometer_clean_cycles = 42

    # Enum-like status attributes (as MagicMock)
    robot.hopper_status = MagicMock()
    robot.hopper_status.__str__ = lambda self: "OK"
    robot.hopper_status.value = "OK"
    robot.globe_motor_fault_status = MagicMock()
    robot.globe_motor_fault_status.__str__ = lambda self: "NONE"
    robot.pinch_status = MagicMock()
    robot.pinch_status.__str__ = lambda self: "NONE"
    robot.cat_detect = MagicMock()
    robot.cat_detect.__str__ = lambda self: "IDLE"
    robot.firmware_update_status = MagicMock()
    robot.firmware_update_status.__str__ = lambda self: "UP_TO_DATE"
    robot.stm_update_status = MagicMock()
    robot.stm_update_status.__str__ = lambda self: "UP_TO_DATE"
    robot.power_status = MagicMock()
    robot.power_status.__str__ = lambda self: "AC"
    robot.power_status.value = "AC"
    robot.privacy_mode = MagicMock()
    robot.privacy_mode.__str__ = lambda self: "OFF"

    # Status for vacuum
    status_mock = MagicMock()
    status_mock.text = "Ready"
    robot.status = status_mock
    robot.status_code = "RDY"

    # Binary sensor attributes
    robot.is_online = True
    robot.is_drawer_removed = False
    robot.is_bonnet_removed = False
    robot.is_laser_dirty = False
    robot.camera_audio_enabled = True
    robot.is_smart_weight_enabled = True

    # Switch/control attributes
    robot.night_light_mode_enabled = True
    robot.panel_lock_enabled = False
    robot.sleep_mode_enabled = True
    robot.is_sleeping = False

    # Night light (LR5)
    night_light_mode = MagicMock()
    night_light_mode.value = "AUTO"
    robot.night_light_mode = night_light_mode
    robot.night_light_brightness = 75
    robot.night_light_color = "#FF00FF"

    # Panel brightness
    panel_brightness = MagicMock()
    robot.panel_brightness = panel_brightness

    # Wait time
    robot.clean_cycle_wait_time_minutes = 7

    # Sleep schedule data
    robot._data = {
        "sleepSchedules": [
            {"dayOfWeek": 0, "isEnabled": True, "sleepTime": 1320, "wakeTime": 420},
            {"dayOfWeek": 1, "isEnabled": True, "sleepTime": 1320, "wakeTime": 420},
            {"dayOfWeek": 2, "isEnabled": True, "sleepTime": 1320, "wakeTime": 420},
            {"dayOfWeek": 3, "isEnabled": True, "sleepTime": 1320, "wakeTime": 420},
            {"dayOfWeek": 4, "isEnabled": True, "sleepTime": 1320, "wakeTime": 420},
            {"dayOfWeek": 5, "isEnabled": False, "sleepTime": 1380, "wakeTime": 480},
            {"dayOfWeek": 6, "isEnabled": False, "sleepTime": 1380, "wakeTime": 480},
        ]
    }

    # Sleep time sensor attributes
    robot.sleep_mode_start_time = datetime(
        2026, 2, 16, 22, 0, 0, tzinfo=timezone.utc
    )
    robot.sleep_mode_end_time = datetime(
        2026, 2, 17, 7, 0, 0, tzinfo=timezone.utc
    )

    # Vacuum extra attributes
    litter_level_state = MagicMock()
    litter_level_state.value = "NORMAL"
    robot.litter_level_state = litter_level_state
    robot.is_gas_sensor_fault_detected = False
    robot.is_usb_fault_detected = False
    robot.is_hopper_removed = False

    # Async action methods
    robot.start_cleaning = AsyncMock()
    robot.reset_waste_drawer = AsyncMock()
    robot.reset = AsyncMock()
    robot.change_filter = AsyncMock()
    robot.set_night_light = AsyncMock()
    robot.set_panel_lockout = AsyncMock()
    robot.set_power_status = AsyncMock()
    robot.set_wait_time = AsyncMock()
    robot.set_night_light_mode = AsyncMock()
    robot.set_night_light_brightness = AsyncMock()
    robot.set_night_light_color = AsyncMock()
    robot.set_panel_brightness = AsyncMock()
    robot.set_sleep_mode = AsyncMock()
    robot._patch = AsyncMock()
    robot._update_data = MagicMock()

    return robot


@pytest.fixture
def mock_feeder_robot():
    """Return a mock FeederRobot with all attributes."""
    robot = MagicMock()
    robot.serial = "RF-TEST-SERIAL"
    robot.name = "Test Feeder"
    robot.model = "Feeder-Robot"

    # Sensor attributes
    robot.food_level = 60
    robot.next_feeding = datetime(2026, 2, 16, 18, 0, 0, tzinfo=timezone.utc)
    robot.last_feeding = {
        "timestamp": datetime(2026, 2, 16, 8, 0, 0, tzinfo=timezone.utc),
        "amount": 0.25,
        "name": "Breakfast",
    }
    robot.get_food_dispensed_since = MagicMock(return_value=0.5)

    # Binary sensor
    robot.is_online = True

    # Switch attributes
    robot.night_light_mode_enabled = True
    robot.panel_lock_enabled = False
    robot.gravity_mode_enabled = False

    # Select
    robot.meal_insert_size = 0.125

    # Async action methods
    robot.give_snack = AsyncMock()
    robot.set_night_light = AsyncMock()
    robot.set_panel_lockout = AsyncMock()
    robot.set_gravity_mode = AsyncMock()
    robot.set_meal_insert_size = AsyncMock()

    return robot


@pytest.fixture
def mock_pet():
    """Return a mock Pet with all attributes."""
    pet = MagicMock()
    pet.id = "pet-test-id"
    pet.name = "Test Cat"
    pet.weight = 10.5
    pet.estimated_weight = 10.3
    pet.last_weight_reading = 10.5
    pet.gender = MagicMock()
    pet.gender.__str__ = lambda self: "female"
    pet.gender.capitalize = MagicMock(return_value="Female")
    pet.pet_type = MagicMock()
    pet.pet_type.__str__ = lambda self: "cat"
    pet.pet_type.capitalize = MagicMock(return_value="Cat")
    pet.diet = MagicMock()
    pet.diet.__str__ = lambda self: "dry"
    pet.environment_type = MagicMock()
    pet.environment_type.__str__ = lambda self: "indoor"
    pet.birthday = date(2022, 5, 15)
    pet.adoption_date = date(2022, 8, 1)
    pet.breeds = ["Domestic Shorthair"]
    pet.age = 3
    pet.is_fixed = True
    pet.is_healthy = True
    pet.health_concerns = []
    pet.is_active = True
    pet.image_url = "https://example.com/cat.jpg"
    pet.pet_tag_id = "TAG-001"
    pet.weight_id_feature_enabled = True

    # Weight history
    wh_entry1 = MagicMock()
    wh_entry1.timestamp = datetime(2026, 2, 16, 10, 0, 0, tzinfo=timezone.utc)
    wh_entry1.weight = 10.55
    wh_entry2 = MagicMock()
    wh_entry2.timestamp = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
    wh_entry2.weight = 10.42
    pet.weight_history = [wh_entry1, wh_entry2]

    # Visits method
    pet.get_visits_since = MagicMock(return_value=3)

    # Async methods
    pet.refresh = AsyncMock()
    pet.fetch_weight_history = AsyncMock()

    return pet


@pytest.fixture
def mock_account(mock_litter_robot, mock_feeder_robot, mock_pet):
    """Return a mock Account with robots and pets."""
    account = MagicMock()
    account.robots = [mock_litter_robot, mock_feeder_robot]
    account.pets = [mock_pet]
    account.connect = AsyncMock()
    account.refresh_robots = AsyncMock()
    account.load_pets = AsyncMock()
    return account


@pytest.fixture
def mock_coordinator():
    """Return a mock DataUpdateCoordinator."""
    coordinator = MagicMock()
    coordinator.async_add_listener = MagicMock(return_value=MagicMock())
    coordinator.async_request_refresh = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = True
    coordinator.async_set_updated_data = MagicMock()
    return coordinator


@pytest.fixture
def mock_hub(mock_account, mock_coordinator):
    """Return a mock LitterRobotHub."""
    hub = MagicMock()
    hub.account = mock_account
    hub.coordinator = mock_coordinator
    hub.hass = MagicMock()
    return hub
