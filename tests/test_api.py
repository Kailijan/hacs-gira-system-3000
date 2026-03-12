"""Tests for the Gira BLE API command layer."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.gira_system_3000.api import (
    GiraBleApi,
    _command_down,
    _command_stop,
    _command_up,
    _command_value,
)


# ---------------------------------------------------------------------------
# Pure command-byte tests – no HA or BLE stack required
# ---------------------------------------------------------------------------


class TestCommandBytes:
    """Verify that the BLE command builder functions produce correct byte sequences."""

    def test_command_stop_bytes(self):
        """STOP command uses opcode 0xfd in byte 4."""
        assert _command_stop() == bytes([0xF6, 0x03, 0x20, 0x01, 0xFD, 0x10, 0x01, 0x00])

    def test_command_up_bytes(self):
        """UP command is a value command with payload 0x00 (fully open)."""
        assert _command_up() == bytes([0xF6, 0x03, 0x20, 0x01, 0xFC, 0x10, 0x01, 0x00])

    def test_command_down_bytes(self):
        """DOWN command is a value command with payload 0xFF (fully closed)."""
        assert _command_down() == bytes([0xF6, 0x03, 0x20, 0x01, 0xFC, 0x10, 0x01, 0xFF])

    def test_command_value_embeds_payload_in_last_byte(self):
        """value command places the given payload in the final byte."""
        assert _command_value(0x80) == bytes([0xF6, 0x03, 0x20, 0x01, 0xFC, 0x10, 0x01, 0x80])

    def test_command_value_zero_payload(self):
        assert _command_value(0x00)[-1] == 0x00

    def test_command_value_max_payload(self):
        assert _command_value(0xFF)[-1] == 0xFF

    def test_command_value_header_bytes_are_constant(self):
        """The first 7 bytes are always the same for every value command."""
        header = bytes([0xF6, 0x03, 0x20, 0x01, 0xFC, 0x10, 0x01])
        assert _command_value(0x42)[:7] == header

    def test_command_stop_differs_from_value_command(self):
        """STOP uses a different opcode (byte 4) than the value command."""
        assert _command_stop()[4] != _command_value(0x00)[4]


# ---------------------------------------------------------------------------
# GiraBleApi queue tests – mocks asyncio.create_task so no event loop needed
# ---------------------------------------------------------------------------


def _make_api() -> GiraBleApi:
    """Create a GiraBleApi instance with the background task suppressed."""
    hass = MagicMock()
    with patch("asyncio.create_task", return_value=MagicMock()):
        api = GiraBleApi(hass, "AA:BB:CC:DD:EE:FF")
    return api


class TestGiraBleApiQueue:
    """Verify that public send_* methods enqueue the correct command bytes."""

    def test_send_command_up_queues_up_bytes(self):
        api = _make_api()
        api.send_command_up()
        assert api._commandQueue.get_nowait() == _command_up()

    def test_send_command_down_queues_down_bytes(self):
        api = _make_api()
        api.send_command_down()
        assert api._commandQueue.get_nowait() == _command_down()

    def test_send_command_stop_queues_stop_bytes(self):
        api = _make_api()
        api.send_command_stop()
        assert api._commandQueue.get_nowait() == _command_stop()

    def test_send_command_zero_percent_maps_to_payload_zero(self):
        """0 % must map to gira payload 0x00."""
        api = _make_api()
        api.send_command(0)
        assert api._commandQueue.get_nowait() == _command_value(0)

    def test_send_command_hundred_percent_maps_to_payload_255(self):
        """100 % must map to gira payload 0xFF (255)."""
        api = _make_api()
        api.send_command(100)
        assert api._commandQueue.get_nowait() == _command_value(255)

    def test_send_command_fifty_percent_maps_to_payload_127(self):
        """50 % maps to round(50 * 2.55) = 127 (floating-point: 50*2.55 ≈ 127.4999)."""
        api = _make_api()
        api.send_command(50)
        assert api._commandQueue.get_nowait() == _command_value(127)

    def test_send_command_one_percent(self):
        """1 % maps to round(1 * 2.55) = 3."""
        api = _make_api()
        api.send_command(1)
        assert api._commandQueue.get_nowait() == _command_value(round(1 * 2.55))

    def test_send_command_negative_percent_is_rejected(self):
        """Negative percentages must not enqueue any command."""
        api = _make_api()
        api.send_command(-1)
        assert api._commandQueue.empty()

    def test_send_command_over_hundred_is_rejected(self):
        """Percentages > 100 must not enqueue any command."""
        api = _make_api()
        api.send_command(101)
        assert api._commandQueue.empty()

    def test_multiple_commands_are_queued_in_order(self):
        """Commands must be dequeued in FIFO order."""
        api = _make_api()
        api.send_command_up()
        api.send_command_stop()
        api.send_command_down()
        assert api._commandQueue.get_nowait() == _command_up()
        assert api._commandQueue.get_nowait() == _command_stop()
        assert api._commandQueue.get_nowait() == _command_down()

    def test_queue_is_empty_after_all_commands_consumed(self):
        api = _make_api()
        api.send_command_up()
        api._commandQueue.get_nowait()
        assert api._commandQueue.empty()
