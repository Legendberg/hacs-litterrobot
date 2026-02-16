"""Support for Litter-Robot button entities."""
from __future__ import annotations

from typing import Callable

from pylitterbot.robot import Robot

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LitterRobotControlEntity, is_litter_robot, is_feeder_robot, is_lr5
from .hub import LitterRobotHub


class LitterRobotCleanButton(LitterRobotControlEntity, ButtonEntity):
    """Litter-Robot Clean Cycle button."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:play-circle"

    async def async_press(self) -> None:
        """Start a clean cycle."""
        await self.perform_action_and_refresh(self.robot.start_cleaning)


class LitterRobotResetButton(LitterRobotControlEntity, ButtonEntity):
    """Litter-Robot 5 Reset button."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:restart"

    async def async_press(self) -> None:
        """Perform a remote reset."""
        await self.perform_action_and_refresh(self.robot.reset)


class LitterRobotResetWasteDrawerButton(LitterRobotControlEntity, ButtonEntity):
    """Litter-Robot Reset Waste Drawer button."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:delete-empty"

    async def async_press(self) -> None:
        """Reset the waste drawer level."""
        await self.robot.reset_waste_drawer()
        self.coordinator.async_set_updated_data(True)


class FeederRobotGiveSnackButton(LitterRobotControlEntity, ButtonEntity):
    """Feeder-Robot Give Snack button."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:food-drumstick"

    async def async_press(self) -> None:
        """Dispense a snack."""
        await self.perform_action_and_refresh(self.robot.give_snack)


class LitterRobotChangeFilterButton(LitterRobotControlEntity, ButtonEntity):
    """Litter-Robot 5 Change Filter button."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:air-filter"

    async def async_press(self) -> None:
        """Reset the filter replacement counter."""
        await self.robot.change_filter()
        self.coordinator.async_set_updated_data(True)


ROBOT_BUTTONS: list[
    tuple[type[LitterRobotControlEntity], str, Callable[[Robot], bool] | None]
] = [
    (LitterRobotCleanButton, "Clean Cycle", None),
    (LitterRobotResetWasteDrawerButton, "Reset Waste Drawer", None),
    (LitterRobotResetButton, "Recalibrate", is_lr5),
    (LitterRobotChangeFilterButton, "Change Filter", is_lr5),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Litter-Robot button entities using config entry."""
    hub: LitterRobotHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for robot in hub.account.robots:
        if is_litter_robot(robot):
            for button_class, entity_type, model_filter in ROBOT_BUTTONS:
                if model_filter is not None and not model_filter(robot):
                    continue
                entities.append(
                    button_class(robot=robot, entity_type=entity_type, hub=hub)
                )
        elif is_feeder_robot(robot):
            entities.append(
                FeederRobotGiveSnackButton(robot=robot, entity_type="Give Snack", hub=hub)
            )

    async_add_entities(entities, True)
