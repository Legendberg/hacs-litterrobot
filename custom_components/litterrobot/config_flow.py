"""Config flow for Litter-Robot integration."""
import logging

from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_NOTIFY_CRITICAL,
    CONF_NOTIFY_EVENTS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_WARNING,
    DEFAULT_CRITICAL_EVENTS,
    DEFAULT_NOTIFY_EVENTS,
    DEFAULT_WARNING_EVENTS,
    DOMAIN,
    EVENT_TYPES,
)
from .hub import LitterRobotHub

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Litter-Robot."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_USERNAME: user_input[CONF_USERNAME]})

            hub = LitterRobotHub(self.hass, user_input)
            try:
                await hub.login()
            except LitterRobotLoginException:
                errors["base"] = "invalid_auth"
            except LitterRobotException:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Litter-Robot options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage notification options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Discover available notify services
        notify_services = [""]
        services = self.hass.services.async_services()
        if "notify" in services:
            notify_services += sorted(services["notify"].keys())

        options = self.config_entry.options
        event_options = {e: e.replace("_", " ").title() for e in EVENT_TYPES}

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    default=options.get(CONF_NOTIFY_SERVICE, ""),
                ): vol.In(notify_services),
                vol.Optional(
                    CONF_NOTIFY_EVENTS,
                    default=options.get(CONF_NOTIFY_EVENTS, DEFAULT_NOTIFY_EVENTS),
                ): cv.multi_select(event_options),
                vol.Optional(
                    CONF_NOTIFY_WARNING,
                    default=options.get(CONF_NOTIFY_WARNING, DEFAULT_WARNING_EVENTS),
                ): cv.multi_select(event_options),
                vol.Optional(
                    CONF_NOTIFY_CRITICAL,
                    default=options.get(CONF_NOTIFY_CRITICAL, DEFAULT_CRITICAL_EVENTS),
                ): cv.multi_select(event_options),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
