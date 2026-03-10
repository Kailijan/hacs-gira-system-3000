# Home Assistant Dev Container Setup

This dev container provides a complete Home Assistant development environment with your `gira_system_3000` custom component pre-mounted and ready to test.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- VS Code with "Dev Containers" extension installed

### Launch the Dev Container

1. **Open in VS Code Dev Container:**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Select "Dev Containers: Reopen in Container"
   - Wait for the container to build and start

2. **Access Home Assistant:**
   - Once running, navigate to `http://localhost:8123`
   - Complete the initial setup wizard
   - Add the `gira_system_3000` integration through Settings > Devices & Services

### Directory Structure

```
.devcontainer/
├── devcontainer.json       # Dev container configuration
├── docker-compose.yml      # Docker Compose configuration
└── configuration.yaml      # Home Assistant config with debug logging
```

## Features

- **Full Home Assistant environment** running in Docker
- **Custom component auto-mounted** at `/config/custom_components/gira_system_3000`
- **Debug logging enabled** for the integration in Home Assistant
- **Python development tools** including Pylance and Ruff
- **Hot reload support** - changes to the component are reflected immediately

## Development Workflow

1. **Edit component files** in your workspace (they're automatically mounted)
2. **Check Home Assistant logs** in the Web UI (Settings > System > Logs)
3. **Reload integrations** without full restart:
   - Go to Settings > Developer Tools > YAML
   - Run `homeassistant.reload_custom_components`

## Common Tasks

### View Logs
```bash
# In the dev container terminal:
docker logs homeassistant-dev -f
```

### Restart Home Assistant
```bash
docker restart homeassistant-dev
```

### Access the Config Directory
The configuration is stored in the `ha-config` Docker volume. To inspect it:
```bash
docker volume inspect hacs-gira-system-3000_ha-config
```

### Install Additional Dependencies
Edit `manifest.json` to add any required Python packages in the `requirements` field, then restart the container.

## Bluetooth Configuration (WSL2)

### Prerequisites
WSL2 does not have native Bluetooth support. To use Bluetooth with Home Assistant, you need to set up USB device passthrough.

### Setup Steps

1. **Install USBIPD on Windows (PowerShell as Administrator):**
   ```powershell
   winget install usbipd
   ```

2. **List USB devices to find your Bluetooth adapter:**
   ```powershell
   usbipd list
   ```
   Look for a device named "Bluetooth" or similar. Note its Bus ID (e.g., `2-4`).

3. **If the device is not shared make sure to bin it:**

```powershell
usbipd bind --busid <BUS_ID>
```
Replace `<BUS_ID>` with the actual Bus ID from step 2.

3. **Attach the Bluetooth adapter to WSL2:**
   ```powershell
   usbipd attach --wsl --busid=<BUS_ID>
   ```
   Replace `<BUS_ID>` with the actual Bus ID from step 2.

4. **Verify in WSL2:**
   ```bash
   lsusb | grep -i bluetooth
   ```

5. **Rebuild the Dev Container:**
   - Press `Ctrl+Shift+P` in VS Code
   - Select "Dev Containers: Rebuild Container"
   - The container will install bluez and necessary Bluetooth tools

6. **Verify Bluetooth in the Container:**
   ```bash
   # Inside the container
   hciconfig
   bluetoothctl list
   ```

### Auto-Attach on WSL2 Startup (Optional)

Create a Windows Task Scheduler task to auto-attach the USB device:

1. Open Task Scheduler
2. Create Basic Task → Name: "Attach Bluetooth to WSL2"
3. Trigger: "At startup"
4. Action: "Start a program"
   - Program: `C:\Windows\System32\wsl.exe`
   - Arguments: `--mount-usb /dev/bus/usb/002/004` (adjust path based on your device)

### Troubleshooting Bluetooth

**Device not found in WSL2:**
- Ensure the device is attached: `usbipd list --attached`
- Reattach if needed: `usbipd detach --busid=<BUS_ID>` then reattach

**Cannot connect to Bluetooth device:**
1. Check container logs: `docker logs homeassistant-dev -f`
2. Verify bluez is running: `systemctl status bluetooth`
3. Restart bluetooth: `systemctl restart bluetooth`

**Permission denied errors:**
- The container already runs with `privileged: true`, which should handle permissions
- If issues persist, check udev rules in the container

## Troubleshooting

### Component Not Loading
1. Check Home Assistant logs for errors
2. Verify `manifest.json` is properly formatted
3. Ensure `__init__.py` has the correct `DOMAIN` value
4. Try reloading custom components through Developer Tools

### Container Won't Start
1. Make sure ports 8123 isn't already in use
2. Check Docker logs: `docker logs homeassistant-dev`
3. Rebuild the container: `Dev Containers: Rebuild Container`

## Further Development

When ready to expand the integration:
- Implement actual device discovery in `config_flow.py`
- Add sensor/cover entities in `sensor.py` and `cover.py`
- Add any custom requirements to `manifest.json`
- Add entity integration tests in the `tests/` directory
