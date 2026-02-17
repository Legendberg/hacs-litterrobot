"""Tests for the Litter-Robot device triggers."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE

from custom_components.litterrobot.device_trigger import (
    TRIGGER_TYPES,
    TRIGGER_SCHEMA,
    async_get_triggers,
    async_attach_trigger,
)
from custom_components.litterrobot.const import DOMAIN


class TestTriggerTypes:
    """Tests for trigger type definitions."""

    def test_all_types_defined(self):
        assert "clean_cycle_complete" in TRIGGER_TYPES
        assert "waste_drawer_full" in TRIGGER_TYPES
        assert "robot_online" in TRIGGER_TYPES
        assert "robot_offline" in TRIGGER_TYPES
        assert "pet_visit" in TRIGGER_TYPES

    def test_trigger_count(self):
        assert len(TRIGGER_TYPES) == 9


class TestGetTriggers:
    """Tests for async_get_triggers."""

    async def test_robot_triggers(self, hass):
        """Test getting triggers for a robot device."""
        device_id = "test_device_id"
        mock_device = MagicMock()
        mock_device.identifiers = {(DOMAIN, "LR5-TEST-SERIAL")}
        mock_device.model = "Litter-Robot 5"

        with patch(
            "custom_components.litterrobot.device_trigger.dr.async_get"
        ) as mock_dr:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = mock_device
            mock_dr.return_value = mock_registry

            triggers = await async_get_triggers(hass, device_id)

        assert len(triggers) == 8
        types = {t[CONF_TYPE] for t in triggers}
        assert types == {
            "clean_cycle_complete", "waste_drawer_full", "robot_online", "robot_offline",
            "drawer_removed", "bonnet_removed", "pinch_detected", "motor_fault",
        }

        for trigger in triggers:
            assert trigger[CONF_PLATFORM] == "device"
            assert trigger[CONF_DEVICE_ID] == device_id
            assert trigger[CONF_DOMAIN] == DOMAIN

    async def test_pet_triggers(self, hass):
        """Test getting triggers for a pet device."""
        device_id = "test_pet_device_id"
        mock_device = MagicMock()
        mock_device.identifiers = {(DOMAIN, "pet-123")}
        mock_device.model = "Pet"

        with patch(
            "custom_components.litterrobot.device_trigger.dr.async_get"
        ) as mock_dr:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = mock_device
            mock_dr.return_value = mock_registry

            triggers = await async_get_triggers(hass, device_id)

        assert len(triggers) == 1
        assert triggers[0][CONF_TYPE] == "pet_visit"

    async def test_unknown_device(self, hass):
        """Test getting triggers for an unknown device."""
        with patch(
            "custom_components.litterrobot.device_trigger.dr.async_get"
        ) as mock_dr:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = None
            mock_dr.return_value = mock_registry

            triggers = await async_get_triggers(hass, "unknown_id")

        assert triggers == []

    async def test_no_matching_identifier(self, hass):
        """Test getting triggers when no DOMAIN identifier matches."""
        device_id = "other_device"
        mock_device = MagicMock()
        mock_device.identifiers = {("other_domain", "some-serial")}
        mock_device.model = "Something"

        with patch(
            "custom_components.litterrobot.device_trigger.dr.async_get"
        ) as mock_dr:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = mock_device
            mock_dr.return_value = mock_registry

            triggers = await async_get_triggers(hass, device_id)

        assert triggers == []

    async def test_attach_trigger(self, hass):
        """Test attaching a trigger."""
        mock_device = MagicMock()
        mock_device.identifiers = {(DOMAIN, "LR5-TEST-SERIAL")}

        config = {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: "test_device_id",
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: "clean_cycle_complete",
        }
        action = AsyncMock()
        trigger_info = MagicMock()

        with patch(
            "custom_components.litterrobot.device_trigger.dr.async_get"
        ) as mock_dr, patch(
            "custom_components.litterrobot.device_trigger.event_trigger.TRIGGER_SCHEMA"
        ) as mock_schema, patch(
            "custom_components.litterrobot.device_trigger.event_trigger.async_attach_trigger"
        ) as mock_attach:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = mock_device
            mock_dr.return_value = mock_registry
            mock_schema.return_value = MagicMock()
            mock_attach.return_value = AsyncMock()

            await async_attach_trigger(hass, config, action, trigger_info)

            mock_attach.assert_called_once()
