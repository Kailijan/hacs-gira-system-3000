"""Tests for the Gira BLE coordinator."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.gira_system_3000.coordinator import GiraBleCoordinator


@pytest.fixture
def mock_api():
    """Return a mocked GiraBleApi."""
    return MagicMock()


@pytest.fixture
def coordinator(hass, mock_api):
    """Return a GiraBleCoordinator wired to a mocked API."""
    return GiraBleCoordinator(hass, mock_api)


class TestGiraBleCoordinatorDelegation:
    """Verify that coordinator methods delegate correctly to the API."""

    def test_open_cover_calls_send_command_up(self, coordinator, mock_api):
        coordinator.open_cover()
        mock_api.send_command_up.assert_called_once()

    def test_close_cover_calls_send_command_down(self, coordinator, mock_api):
        coordinator.close_cover()
        mock_api.send_command_down.assert_called_once()

    def test_stop_cover_calls_send_command_stop(self, coordinator, mock_api):
        coordinator.stop_cover()
        mock_api.send_command_stop.assert_called_once()

    def test_set_cover_position_passes_value_to_api(self, coordinator, mock_api):
        coordinator.set_cover_position(75)
        mock_api.send_command.assert_called_once_with(75)

    def test_set_cover_position_zero(self, coordinator, mock_api):
        coordinator.set_cover_position(0)
        mock_api.send_command.assert_called_once_with(0)

    def test_set_cover_position_hundred(self, coordinator, mock_api):
        coordinator.set_cover_position(100)
        mock_api.send_command.assert_called_once_with(100)


class TestGiraBleCoordinatorNotifications:
    """Verify the sensor notification handler parses incoming BLE data."""

    def _make_sensor_frame(self, temperature: int = 20, lux_raw: int = 0) -> bytes:
        """Build a minimal notification frame that triggers sensor parsing."""
        data = bytearray(12)
        data[0] = 0xFB  # header
        data[4] = 0x0B  # sensor opcode
        data[8] = temperature
        data[9] = (lux_raw >> 8) & 0xFF
        data[10] = lux_raw & 0xFF
        return bytes(data)

    def test_notification_handler_stores_temperature(self, coordinator):
        coordinator.data = {}
        frame = self._make_sensor_frame(temperature=22)
        with patch.object(coordinator, "async_update_listeners"):
            coordinator.notification_handler(None, frame)
        assert coordinator.data["temperature"] == 22

    def test_notification_handler_stores_brightness_scaled(self, coordinator):
        """Brightness value must be scaled by factor 3.68."""
        coordinator.data = {}
        # lux_raw = 10 → round(10 * 3.68) = 37
        frame = self._make_sensor_frame(lux_raw=10)
        with patch.object(coordinator, "async_update_listeners"):
            coordinator.notification_handler(None, frame)
        assert coordinator.data["brightness"] == 37

    def test_notification_handler_combines_lux_high_and_low_bytes(self, coordinator):
        """lux_raw is a 16-bit big-endian value spanning bytes 9 and 10."""
        coordinator.data = {}
        # lux_raw = 0x0100 = 256 → round(256 * 3.68) = 942
        frame = self._make_sensor_frame(lux_raw=256)
        with patch.object(coordinator, "async_update_listeners"):
            coordinator.notification_handler(None, frame)
        assert coordinator.data["brightness"] == round(256 * 3.68)

    def test_notification_handler_calls_notify_listeners(self, coordinator):
        """All registered listeners must be notified after parsing sensor data."""
        coordinator.data = {}
        frame = self._make_sensor_frame()
        with patch.object(coordinator, "async_update_listeners") as mock_notify:
            coordinator.notification_handler(None, frame)
        mock_notify.assert_called_once()

    def test_notification_handler_ignores_non_sensor_frames(self, coordinator):
        """Frames with a different header or opcode must not update coordinator data."""
        coordinator.data = {}
        data = bytearray(12)
        data[0] = 0xAA  # unexpected header
        data[4] = 0x0B
        coordinator.notification_handler(None, bytes(data))
        assert coordinator.data == {}
