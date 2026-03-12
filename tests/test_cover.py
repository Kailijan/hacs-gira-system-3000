"""Tests for the Gira cover entity."""
from unittest.mock import MagicMock

import pytest
from homeassistant.components.cover import CoverDeviceClass, CoverEntityFeature

from custom_components.gira_system_3000.cover import GiraBleCover


@pytest.fixture
def mock_coordinator():
    """Return a mocked GiraBleCoordinator."""
    return MagicMock()


@pytest.fixture
def cover(mock_coordinator):
    """Return a GiraBleCover with its HA state write method mocked out."""
    entity = GiraBleCover(mock_coordinator)
    entity.hass = MagicMock()
    entity.async_write_ha_state = MagicMock()
    return entity


class TestGiraBleCoverAttributes:
    """Verify static entity attributes."""

    def test_device_class_is_blind(self, cover):
        assert cover._attr_device_class == CoverDeviceClass.BLIND

    def test_supports_open(self, cover):
        assert cover._attr_supported_features & CoverEntityFeature.OPEN

    def test_supports_close(self, cover):
        assert cover._attr_supported_features & CoverEntityFeature.CLOSE

    def test_supports_stop(self, cover):
        assert cover._attr_supported_features & CoverEntityFeature.STOP

    def test_supports_set_position(self, cover):
        assert cover._attr_supported_features & CoverEntityFeature.SET_POSITION

    def test_initial_state_is_closed(self, cover):
        assert cover._attr_is_closed is True

    def test_initial_position_is_zero(self, cover):
        assert cover._attr_current_cover_position == 0


class TestGiraBleCoverOpen:
    """Verify open_cover behaviour."""

    async def test_open_cover_calls_coordinator(self, cover, mock_coordinator):
        await cover.async_open_cover()
        mock_coordinator.open_cover.assert_called_once()

    async def test_open_cover_marks_entity_as_open(self, cover):
        await cover.async_open_cover()
        assert cover._attr_is_closed is False

    async def test_open_cover_sets_position_to_100(self, cover):
        await cover.async_open_cover()
        assert cover._attr_current_cover_position == 100

    async def test_open_cover_writes_ha_state(self, cover):
        await cover.async_open_cover()
        cover.async_write_ha_state.assert_called()


class TestGiraBleCoverClose:
    """Verify close_cover behaviour."""

    async def test_close_cover_calls_coordinator(self, cover, mock_coordinator):
        await cover.async_close_cover()
        mock_coordinator.close_cover.assert_called_once()

    async def test_close_cover_marks_entity_as_closed(self, cover):
        cover._attr_is_closed = False
        await cover.async_close_cover()
        assert cover._attr_is_closed is True

    async def test_close_cover_sets_position_to_zero(self, cover):
        cover._attr_current_cover_position = 100
        await cover.async_close_cover()
        assert cover._attr_current_cover_position == 0

    async def test_close_cover_writes_ha_state(self, cover):
        await cover.async_close_cover()
        cover.async_write_ha_state.assert_called()


class TestGiraBleCoverStop:
    """Verify stop_cover behaviour."""

    async def test_stop_cover_calls_coordinator(self, cover, mock_coordinator):
        await cover.async_stop_cover()
        mock_coordinator.stop_cover.assert_called_once()

    async def test_stop_cover_writes_ha_state(self, cover):
        await cover.async_stop_cover()
        cover.async_write_ha_state.assert_called()


class TestGiraBleCoverSetPosition:
    """Verify set_cover_position behaviour, including the Gira inversion."""

    async def test_position_is_stored_on_entity(self, cover):
        await cover.async_set_cover_position(position=60)
        assert cover._attr_current_cover_position == 60

    async def test_position_is_inverted_before_sending_to_device(
        self, cover, mock_coordinator
    ):
        """The Gira device uses an inverted scale: HA 30 % → Gira 70 %."""
        await cover.async_set_cover_position(position=30)
        mock_coordinator.set_cover_position.assert_called_once_with(70)

    async def test_position_100_inverts_to_zero_for_device(
        self, cover, mock_coordinator
    ):
        await cover.async_set_cover_position(position=100)
        mock_coordinator.set_cover_position.assert_called_once_with(0)

    async def test_position_zero_inverts_to_100_for_device(
        self, cover, mock_coordinator
    ):
        await cover.async_set_cover_position(position=0)
        mock_coordinator.set_cover_position.assert_called_once_with(100)

    async def test_position_zero_marks_cover_as_closed(self, cover):
        await cover.async_set_cover_position(position=0)
        assert cover._attr_is_closed is True

    async def test_position_nonzero_marks_cover_as_open(self, cover):
        await cover.async_set_cover_position(position=50)
        assert cover._attr_is_closed is False

    async def test_set_position_writes_ha_state(self, cover):
        await cover.async_set_cover_position(position=50)
        cover.async_write_ha_state.assert_called()
