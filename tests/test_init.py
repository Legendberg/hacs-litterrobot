"""Tests for the Litter-Robot integration setup.

Tests call the custom component's async_setup_entry/async_unload_entry directly
to avoid conflicts with the built-in HA litterrobot integration.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot import async_setup_entry, async_unload_entry, PLATFORMS
from custom_components.litterrobot.const import DOMAIN


def _make_mock_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {"username": "test@example.com", "password": "test_password"}
    entry.options = {}
    entry.title = "test@example.com"
    entry.domain = DOMAIN
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()
    return entry


async def test_setup_entry_success(hass, mock_account):
    """Test successful setup of a config entry."""
    entry = _make_mock_entry()
    hass.data.setdefault(DOMAIN, {})

    # Patch forward_entry_setups to avoid loading platforms
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with patch(
        "custom_components.litterrobot.hub.Account", return_value=mock_account
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.entry_id in hass.data[DOMAIN]
    hub = hass.data[DOMAIN][entry.entry_id]
    assert hub.logged_in is True
    # Verify update listener was registered
    entry.async_on_unload.assert_called_once()


async def test_setup_entry_login_failure(hass):
    """Test login failure returns False."""
    from pylitterbot.exceptions import LitterRobotLoginException

    entry = _make_mock_entry()
    hass.data.setdefault(DOMAIN, {})

    mock_account = MagicMock()
    mock_account.connect = AsyncMock(side_effect=LitterRobotLoginException)

    with patch(
        "custom_components.litterrobot.hub.Account", return_value=mock_account
    ):
        result = await async_setup_entry(hass, entry)

    assert result is False


async def test_setup_entry_connection_error(hass):
    """Test connection error raises ConfigEntryNotReady."""
    from pylitterbot.exceptions import LitterRobotException
    from homeassistant.exceptions import ConfigEntryNotReady

    entry = _make_mock_entry()
    hass.data.setdefault(DOMAIN, {})

    mock_account = MagicMock()
    mock_account.connect = AsyncMock(side_effect=LitterRobotException)

    with patch(
        "custom_components.litterrobot.hub.Account", return_value=mock_account
    ), pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)


async def test_unload_entry(hass, mock_account):
    """Test unloading a config entry."""
    entry = _make_mock_entry()
    hass.data.setdefault(DOMAIN, {})

    # Patch forward_entry_setups to avoid loading platforms
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with patch(
        "custom_components.litterrobot.hub.Account", return_value=mock_account
    ):
        await async_setup_entry(hass, entry)

    assert entry.entry_id in hass.data[DOMAIN]

    # Mock the unload_platforms call
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, entry)

    assert result is True
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_setup_passes_entry_to_hub(hass, mock_account):
    """Test that setup passes the full entry (not just data) to hub."""
    entry = _make_mock_entry()
    hass.data.setdefault(DOMAIN, {})
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with patch(
        "custom_components.litterrobot.hub.Account", return_value=mock_account
    ):
        await async_setup_entry(hass, entry)

    hub = hass.data[DOMAIN][entry.entry_id]
    assert hub._entry is entry
    assert hub._data == entry.data


async def test_options_update_reloads(hass, mock_account):
    """Test that options update listener triggers reload."""
    from custom_components.litterrobot import _async_update_options

    entry = _make_mock_entry()
    hass.config_entries.async_reload = AsyncMock()

    await _async_update_options(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)
