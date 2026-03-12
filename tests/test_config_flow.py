"""Tests for the Gira System 3000 config flow."""
from unittest.mock import patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS, CONF_NAME

from custom_components.gira_system_3000.const import DOMAIN, SVC_UUID


def _make_discovery_info(
    address: str = "AA:BB:CC:DD:EE:FF",
    name: str = "GiraBlind",
) -> BluetoothServiceInfoBleak:
    """Build a minimal BluetoothServiceInfoBleak suitable for testing."""
    device = BLEDevice(address, name, {})
    advertisement = AdvertisementData(
        local_name=name,
        manufacturer_data={},
        service_data={},
        service_uuids=[SVC_UUID],
        tx_power=None,
        rssi=-60,
        platform_data=(),
    )
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=[SVC_UUID],
        source="local",
        device=device,
        advertisement=advertisement,
        connectable=True,
        time=0.0,
        tx_power=None,
    )


# ---------------------------------------------------------------------------
# User-initiated setup flow
# ---------------------------------------------------------------------------


class TestConfigFlowUser:
    """Tests for the manual user-driven setup flow."""

    async def test_user_step_shows_form_without_input(
        self, hass, mock_bluetooth_dependencies, enable_custom_integrations
    ):
        """Initial call to the user step must return a form."""
        with patch(
            "homeassistant.components.bluetooth.async_discovered_service_info",
            return_value=[],
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
        assert result["type"] == "form"
        assert result["step_id"] == "user"

    async def test_user_step_creates_entry_with_valid_input(
        self, hass, mock_bluetooth_dependencies, enable_custom_integrations
    ):
        """Providing address and name must create a config entry."""
        with patch(
            "homeassistant.components.bluetooth.async_discovered_service_info",
            return_value=[_make_discovery_info()],
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    CONF_NAME: "My Blind",
                },
            )

        assert result["type"] == "create_entry"
        assert result["title"] == "My Blind"
        assert result["data"][CONF_ADDRESS] == "AA:BB:CC:DD:EE:FF"

    async def test_user_step_stores_name_in_entry_data(
        self, hass, mock_bluetooth_dependencies, enable_custom_integrations
    ):
        with patch(
            "homeassistant.components.bluetooth.async_discovered_service_info",
            return_value=[],
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    CONF_NAME: "Living Room Blind",
                },
            )
        assert result["data"][CONF_NAME] == "Living Room Blind"

    async def test_user_step_aborts_on_duplicate_address(
        self, hass, mock_bluetooth_dependencies, enable_custom_integrations
    ):
        """A second entry for the same MAC address must be aborted."""
        data = {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF", CONF_NAME: "Blind"}
        with patch(
            "homeassistant.components.bluetooth.async_discovered_service_info",
            return_value=[],
        ):
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data=data,
            )
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data=data,
            )
        assert result["type"] == "abort"
        assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Bluetooth auto-discovery flow
# ---------------------------------------------------------------------------


class TestConfigFlowBluetooth:
    """Tests for the Bluetooth passive discovery flow."""

    async def test_bluetooth_step_shows_confirmation_form(
        self, hass, mock_bluetooth_dependencies, enable_custom_integrations
    ):
        """Bluetooth discovery should present a confirmation form."""
        discovery = _make_discovery_info()
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=discovery,
        )
        assert result["type"] == "form"
        assert result["step_id"] == "bluetooth_confirm"

    async def test_bluetooth_confirm_creates_entry_on_user_confirm(
        self, hass, mock_bluetooth_dependencies, enable_custom_integrations
    ):
        """Confirming the bluetooth dialog must create a config entry."""
        discovery = _make_discovery_info(
            address="BB:CC:DD:EE:FF:AA", name="GiraBlind"
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=discovery,
        )
        assert result["type"] == "form"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result2["type"] == "create_entry"
        assert result2["data"][CONF_ADDRESS] == "BB:CC:DD:EE:FF:AA"

    async def test_bluetooth_aborts_on_duplicate(
        self, hass, mock_bluetooth_dependencies, enable_custom_integrations
    ):
        """A second Bluetooth discovery for an already-configured device must abort."""
        discovery = _make_discovery_info(address="CC:DD:EE:FF:AA:BB")

        # First discovery creates the entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=discovery,
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

        # Second discovery for the same device should abort
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=discovery,
        )
        assert result2["type"] == "abort"
        assert result2["reason"] == "already_configured"
