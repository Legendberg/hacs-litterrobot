"""Tests for the Litter-Robot text platform."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.litterrobot.text import (
    TEXT_DESCRIPTIONS,
    LitterRobotText,
)


class TestTextDescriptions:
    """Tests for text descriptions."""

    def test_descriptions_count(self):
        assert len(TEXT_DESCRIPTIONS) == 1

    def test_night_light_color_description(self):
        desc = TEXT_DESCRIPTIONS[0]
        assert desc.key == "night_light_color"
        assert desc.entity_type == "Night Light Color"
        assert desc.min_length == 4
        assert desc.max_length == 7
        assert desc.pattern == r"#[0-9A-Fa-f]{3,6}"
        assert desc.icon == "mdi:palette"


class TestLitterRobotText:
    """Tests for LitterRobotText entity."""

    def test_native_value(self, mock_litter_robot, mock_hub):
        """Test night light color returns correct value."""
        desc = TEXT_DESCRIPTIONS[0]
        text = LitterRobotText(mock_litter_robot, mock_hub, desc)
        assert text.native_value == "#FF00FF"

    def test_pattern_attribute(self, mock_litter_robot, mock_hub):
        """Test pattern attribute is set."""
        desc = TEXT_DESCRIPTIONS[0]
        text = LitterRobotText(mock_litter_robot, mock_hub, desc)
        assert text.pattern == r"#[0-9A-Fa-f]{3,6}"

    async def test_set_value(self, mock_litter_robot, mock_hub):
        """Test setting the color value."""
        desc = TEXT_DESCRIPTIONS[0]
        text = LitterRobotText(mock_litter_robot, mock_hub, desc)
        text.hass = MagicMock()

        with patch(
            "custom_components.litterrobot.entity.async_call_later",
            return_value=MagicMock(),
        ):
            await text.async_set_value("#00FF00")

        mock_litter_robot.set_night_light_color.assert_awaited_once_with("#00FF00")
