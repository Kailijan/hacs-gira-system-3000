"""This file contains the API for handling BLE communication with the Gira System 3000 devices."""
import asyncio
import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from custom_components.gira_system_3000.const import CHR_COVER_POSITION_UUID, CHR_UUID, SVC_UUID

_LOGGER = logging.getLogger(__name__)

def _command_stop() -> bytes:
    return bytes([0xf6, 0x03, 0x20, 0x01, 0xfd, 0x10, 0x01, 0x00])

def _command_value(payload: int) -> bytes:
    return bytes([0xf6, 0x03, 0x20, 0x01, 0xfc, 0x10, 0x01, payload])

def _command_up() -> bytes:
    return _command_value(0x00)

def _command_down() -> bytes:
    return _command_value(0xff)


class GiraBleApi:
    def __init__(self, hass: HomeAssistant, address: str):
        self._hass = hass
        # save the BLE MAC address for connection
        self._address = address
        self._lock = asyncio.Lock()
        self._connection_lock = asyncio.Lock()  # Prevent concurrent connection attempts
        self._commandQueue: asyncio.Queue[bytes] = asyncio.Queue()
        self._client: BleakClient | None = None
        self._cover_position_callback = None
        self._commandTask = asyncio.create_task(self._command_executor())

    def __del__(self):
        self._commandTask.cancel()

    async def _ensure_connected(self) -> BleakClient | None:
        """Ensure we have an active connection, reusing existing one if possible."""
        async with self._connection_lock:
            # Check if existing connection is still alive
            if self._client and self._client.is_connected:
                _LOGGER.debug("Reusing existing connection to device %s", self._address)
                return self._client
            
            # Disconnect stale connection if any
            if self._client:
                try:
                    await self._client.disconnect()
                except Exception as e:
                    _LOGGER.debug("Error disconnecting stale connection: %s", e)
                self._client = None
                await asyncio.sleep(0.5)  # Give BlueZ time to release the connection

            # Establish new connection
            try:
                ble_device = bluetooth.async_ble_device_from_address(self._hass, self._address, connectable=True)
                if not ble_device:
                    _LOGGER.error("Unable to find Gira Switch at address %s", self._address)
                    return None

                def _get_ble_device() -> BLEDevice | None:
                    return bluetooth.async_ble_device_from_address(
                        self._hass, self._address, connectable=True
                    )

                _LOGGER.debug("Attempting to connect to device %s", self._address)
                self._client = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    ble_device.address,
                    disconnected_callback=self._handle_disconnect,
                    ble_device_callback=_get_ble_device,
                )
                _LOGGER.debug("Successfully connected to device %s", self._address)
                await self._setup_notifications(self._client)
                return self._client
            except Exception as e:
                _LOGGER.error("Failed to establish connection to %s: %s", self._address, e, exc_info=True)
                self._client = None
                return None

    def _handle_disconnect(self, client: BleakClient) -> None:
        """Handle unexpected disconnect from the device."""
        _LOGGER.debug("Device %s disconnected unexpectedly", self._address)

    async def _disconnect(self):
        """Safely disconnect the client."""
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                _LOGGER.debug("Error during disconnect: %s", e)
            finally:
                self._client = None

    async def _command_executor(self):
        """Maintains the Bluetooth connection and processes the command queue."""
        while True:
            try:
                command = await self._commandQueue.get()
                _LOGGER.warning("Processing command from queue: %s", command.hex())
                
                async with self._lock:
                    client = await self._ensure_connected()
                    if not client:
                        _LOGGER.warning("Could not establish connection, command dropped")
                        continue

                    try:
                        service = client.services.get_service(SVC_UUID)
                        if service is None:
                            _LOGGER.error("Unable to get GATT service")
                            await self._disconnect()
                            continue
                        
                        characteristic = service.get_characteristic(CHR_UUID)
                        if characteristic is None:
                            _LOGGER.error("Unable to get GATT characteristic")
                            await self._disconnect()
                            continue
                        
                        await client.write_gatt_char(characteristic, command, True)
                        _LOGGER.info("Successfully sent command to device: %s", command.hex())
                    except Exception as e:
                        _LOGGER.error("Error writing to GATT characteristic: %s", e, exc_info=True)
                        await self._disconnect()
                
                await asyncio.sleep(0.2)  # Small pause between commands
            except asyncio.CancelledError:
                _LOGGER.debug("Command executor task cancelled")
                await self._disconnect()
                break
            except Exception as e:
                _LOGGER.error("Unexpected error in command executor: %s", str(e), exc_info=True)
                await self._disconnect()
                await asyncio.sleep(2)  # Wait longer before retrying after error
    
    def _send_command(self, command: bytes):
        self._commandQueue.put_nowait(command)

    def send_command_up(self):
        _LOGGER.info("Queuing command: UP")
        self._send_command(_command_up())

    def send_command_down(self):
        _LOGGER.info("Queuing command: DOWN")
        self._send_command(_command_down())

    def send_command_stop(self):
        _LOGGER.info("Queuing command: STOP")
        self._send_command(_command_stop())

    def send_command(self, percentage: int):
        _LOGGER.info("Queuing command: %d%", percentage)
        if percentage < 0 or percentage > 100:
            _LOGGER.warning("Invalid percentage: %d", percentage)
            return
        # gira needs a value between 0x00 and 0xff
        gira_payload = round(percentage * 2.55)
        self._send_command(_command_value(gira_payload))


    def set_cover_position_callback(self, callback) -> None:
        """Register a callback to be invoked when a cover position notification arrives."""
        self._cover_position_callback = callback

    async def _setup_notifications(self, client: BleakClient) -> None:
        """Subscribe to cover position notifications and read the current position."""
        try:
            await client.start_notify(CHR_COVER_POSITION_UUID, self._on_cover_position)
            _LOGGER.debug("Subscribed to cover position notifications on %s", self._address)
            # Read the current position so the entity is up-to-date right after connecting.
            data = await client.read_gatt_char(CHR_COVER_POSITION_UUID)
            self._on_cover_position(None, data)
        except Exception as e:
            _LOGGER.warning("Failed to set up cover position notifications: %s", e)

    def _on_cover_position(self, handle: int | None, data: bytearray) -> None:
        """Forward incoming cover position data to the registered callback.

        ``handle`` is the GATT characteristic handle when called from a BLE
        notification, or ``None`` when called after an explicit READ on connect.
        """
        if self._cover_position_callback is not None:
            self._cover_position_callback(handle, data)

    async def notification_handler(self, handle, data):
        """Handle incoming Bluetooth notifications."""
        # Hier könnte die Logik zum Verarbeiten von eingehenden Bluetooth-Daten implementiert werden.
        pass
