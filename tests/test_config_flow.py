"""Tests for the Litter-Robot config flow.

Since the built-in HA litterrobot integration takes precedence over our
custom_component in the test loader, we test the ConfigFlow class directly.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.litterrobot.config_flow import ConfigFlow, OptionsFlowHandler
from custom_components.litterrobot.const import (
    CONF_NOTIFY_CRITICAL,
    CONF_NOTIFY_EVENTS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_WARNING,
    DEFAULT_CRITICAL_EVENTS,
    DEFAULT_NOTIFY_EVENTS,
    DEFAULT_WARNING_EVENTS,
    DOMAIN,
)


MOCK_USER_INPUT = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "test_password",
}


async def test_user_step_success(hass):
    """Test successful user step creates an entry."""
    flow = ConfigFlow()
    flow.hass = hass

    # Show form first
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Submit credentials
    with patch.object(
        flow, "_async_abort_entries_match"
    ), patch(
        "custom_components.litterrobot.config_flow.LitterRobotHub"
    ) as mock_hub_cls:
        mock_hub = MagicMock()
        mock_hub.login = AsyncMock()
        mock_hub_cls.return_value = mock_hub

        result = await flow.async_step_user(user_input=MOCK_USER_INPUT)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_USER_INPUT[CONF_USERNAME]
    assert result["data"] == MOCK_USER_INPUT


async def test_user_step_invalid_auth(hass):
    """Test invalid auth shows error."""
    from pylitterbot.exceptions import LitterRobotLoginException

    flow = ConfigFlow()
    flow.hass = hass

    with patch.object(
        flow, "_async_abort_entries_match"
    ), patch(
        "custom_components.litterrobot.config_flow.LitterRobotHub"
    ) as mock_hub_cls:
        mock_hub = MagicMock()
        mock_hub.login = AsyncMock(side_effect=LitterRobotLoginException)
        mock_hub_cls.return_value = mock_hub

        result = await flow.async_step_user(user_input=MOCK_USER_INPUT)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_step_cannot_connect(hass):
    """Test connection error shows error."""
    from pylitterbot.exceptions import LitterRobotException

    flow = ConfigFlow()
    flow.hass = hass

    with patch.object(
        flow, "_async_abort_entries_match"
    ), patch(
        "custom_components.litterrobot.config_flow.LitterRobotHub"
    ) as mock_hub_cls:
        mock_hub = MagicMock()
        mock_hub.login = AsyncMock(side_effect=LitterRobotException)
        mock_hub_cls.return_value = mock_hub

        result = await flow.async_step_user(user_input=MOCK_USER_INPUT)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_unknown_error(hass):
    """Test unknown error shows error."""
    flow = ConfigFlow()
    flow.hass = hass

    with patch.object(
        flow, "_async_abort_entries_match"
    ), patch(
        "custom_components.litterrobot.config_flow.LitterRobotHub"
    ) as mock_hub_cls:
        mock_hub = MagicMock()
        mock_hub.login = AsyncMock(side_effect=Exception("unexpected"))
        mock_hub_cls.return_value = mock_hub

        result = await flow.async_step_user(user_input=MOCK_USER_INPUT)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_user_step_already_configured(hass):
    """Test abort when already configured.

    _async_abort_entries_match raises AbortFlow which propagates up from
    the config flow step. The flow runner normally catches it.
    """
    from homeassistant.data_entry_flow import AbortFlow

    flow = ConfigFlow()
    flow.hass = hass

    with patch.object(
        flow, "_async_abort_entries_match",
        side_effect=AbortFlow("already_configured"),
    ), pytest.raises(AbortFlow) as exc_info:
        await flow.async_step_user(user_input=MOCK_USER_INPUT)

    assert exc_info.value.reason == "already_configured"


async def test_options_flow_shows_form():
    """Test options flow shows form with defaults."""
    entry = MagicMock()
    entry.options = {}

    mock_hass = MagicMock()
    mock_hass.services.async_services.return_value = {
        "notify": {
            "mobile_app_legendberg": MagicMock(),
            "mobile_app_benjas_ipad": MagicMock(),
            "notify": MagicMock(),
        }
    }

    flow = OptionsFlowHandler(entry)
    flow.hass = mock_hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_saves_options():
    """Test options flow saves user input."""
    entry = MagicMock()
    entry.options = {}

    mock_hass = MagicMock()
    mock_hass.services.async_services.return_value = {"notify": {}}

    flow = OptionsFlowHandler(entry)
    flow.hass = mock_hass

    user_input = {
        CONF_NOTIFY_SERVICE: "mobile_app_legendberg",
        CONF_NOTIFY_EVENTS: ["clean_cycle_complete", "waste_drawer_full"],
        CONF_NOTIFY_CRITICAL: ["waste_drawer_full"],
    }

    result = await flow.async_step_init(user_input=user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == user_input


async def test_options_flow_preserves_existing():
    """Test options flow shows existing options as defaults."""
    existing_options = {
        CONF_NOTIFY_SERVICE: "mobile_app_legendberg",
        CONF_NOTIFY_EVENTS: ["waste_drawer_full", "robot_offline"],
        CONF_NOTIFY_CRITICAL: ["waste_drawer_full"],
    }
    entry = MagicMock()
    entry.options = existing_options

    mock_hass = MagicMock()
    mock_hass.services.async_services.return_value = {
        "notify": {"mobile_app_legendberg": MagicMock()}
    }

    flow = OptionsFlowHandler(entry)
    flow.hass = mock_hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == FlowResultType.FORM
    schema = result["data_schema"]
    assert schema is not None


async def test_options_flow_no_notify_services():
    """Test options flow works when no notify services exist."""
    entry = MagicMock()
    entry.options = {}

    mock_hass = MagicMock()
    mock_hass.services.async_services.return_value = {}

    flow = OptionsFlowHandler(entry)
    flow.hass = mock_hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == FlowResultType.FORM


def test_config_flow_has_options_flow():
    """Test ConfigFlow returns OptionsFlowHandler."""
    entry = MagicMock()
    handler = ConfigFlow.async_get_options_flow(entry)
    assert isinstance(handler, OptionsFlowHandler)
