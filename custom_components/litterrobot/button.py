"""Support for Litter-Robot button entities."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from pylitterbot.robot import Robot

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import (
    LitterRobotControlEntity,
    LitterRobotEntityDescription,
    is_litter_robot,
    is_feeder_robot,
    is_lr5,
)
from .hub import LitterRobotHub


@dataclass(frozen=True, kw_only=True)
class LitterRobotButtonDescription(
    ButtonEntityDescription, LitterRobotEntityDescription
):
    """Describes a Litter-Robot button."""

    press_fn: Callable[[Robot], Coroutine[Any, Any, Any]]
    use_coordinator_update: bool = False


ROBOT_BUTTON_DESCRIPTIONS: tuple[LitterRobotButtonDescription, ...] = (
    LitterRobotButtonDescription(
        key="clean_cycle",
        entity_type="Clean Cycle",
        icon="mdi:play-circle",
        press_fn=lambda r: r.start_cleaning(),
    ),
    LitterRobotButtonDescription(
        key="reset_waste_drawer",
        entity_type="Reset Waste Drawer",
        icon="mdi:delete-empty",
        press_fn=lambda r: r.reset_waste_drawer(),
        use_coordinator_update=True,
    ),
    LitterRobotButtonDescription(
        key="recalibrate",
        entity_type="Recalibrate",
        icon="mdi:restart",
        press_fn=lambda r: r.reset(),
        model_filter=is_lr5,
    ),
    LitterRobotButtonDescription(
        key="change_filter",
        entity_type="Change Filter",
        icon="mdi:air-filter",
        press_fn=lambda r: r.change_filter(),
        use_coordinator_update=True,
        model_filter=is_lr5,
    ),
)

FEEDER_BUTTON_DESCRIPTIONS: tuple[LitterRobotButtonDescription, ...] = (
    LitterRobotButtonDescription(
        key="give_snack",
        entity_type="Give Snack",
        icon="mdi:food-drumstick",
        press_fn=lambda r: r.give_snack(),
    ),
)


class LitterRobotButton(LitterRobotControlEntity, ButtonEntity):
    """Litter-Robot button driven by an entity description."""

    entity_description: LitterRobotButtonDescription

    def __init__(
        self,
        robot: Robot,
        hub: LitterRobotHub,
        description: LitterRobotButtonDescription,
    ) -> None:
        """Initialize a Litter-Robot button."""
        super().__init__(robot, description.entity_type, hub)
        self.entity_description = description

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.use_coordinator_update:
            await self.entity_description.press_fn(self.robot)
            self.coordinator.async_set_updated_data(True)
        else:
            await self.perform_action_and_refresh(
                self.entity_description.press_fn, self.robot
            )


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
            for desc in ROBOT_BUTTON_DESCRIPTIONS:
                if desc.model_filter and not desc.model_filter(robot):
                    continue
                entities.append(LitterRobotButton(robot, hub, desc))
        elif is_feeder_robot(robot):
            for desc in FEEDER_BUTTON_DESCRIPTIONS:
                entities.append(LitterRobotButton(robot, hub, desc))

    async_add_entities(entities, True)
