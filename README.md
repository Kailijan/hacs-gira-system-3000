# hacs-gira-system-3000
HACS Integration for Gira System 3000 bluetooth cover for Home Assistant

[![Tests](https://github.com/Kailijan/hacs-gira-system-3000/actions/workflows/tests.yml/badge.svg)](https://github.com/Kailijan/hacs-gira-system-3000/actions/workflows/tests.yml)

## Installation

### Via HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** → **⋮** → **Custom repositories**.
3. Add `https://github.com/Kailijan/hacs-gira-system-3000` as an **Integration**.
4. Search for **Gira System 3000** and install it.
5. Restart Home Assistant.
6. Go to **Settings** → **Devices & Services** → **Add Integration** and search for **Gira System 3000**.

### Manual installation

1. Copy the `custom_components/gira_system_3000` folder to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration via **Settings** → **Devices & Services**.

## Supported devices

- Gira System 3000 blind/cover actuator (BLE)

## Running the tests

The project ships with a pytest-based test suite that runs entirely without physical hardware.

### Quick start

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=custom_components/gira_system_3000 --cov-report=term-missing
```

### Test layout

| File | What it covers |
|------|----------------|
| `tests/test_api.py` | BLE command byte generation; queue ordering; percentage-to-payload conversion |
| `tests/test_coordinator.py` | Coordinator delegation to the API; sensor notification parsing |
| `tests/test_cover.py` | Cover entity state machine; position inversion; HA state writes |
| `tests/test_config_flow.py` | User setup flow; Bluetooth auto-discovery flow; duplicate-entry prevention |

### Writing new tests

Follow these guidelines when adding tests for new features:

1. **Locate the right test file** – pick the file that matches the module you changed.
2. **Group tests in classes** – use a class per logical behaviour group, e.g. `TestGiraBleCoverOpen`.
3. **Mock BLE/hardware** – never rely on physical hardware. Mock `bleak`, `asyncio.create_task` (for `GiraBleApi` unit tests) and `homeassistant.components.bluetooth` where needed.
4. **Config flow tests** need two fixtures to work correctly in the test runner:
   - `mock_bluetooth_dependencies` – marks the `bluetooth` HA component as already set up so that dependency resolution succeeds without actual hardware.
   - `enable_custom_integrations` – forces HA's loader to re-scan `custom_components/` and discover this integration.
5. **Keep tests fast** – avoid `asyncio.sleep`, real network I/O, and file system writes.
6. **Use descriptive names** – test method names should read as sentences, e.g. `test_position_is_inverted_before_sending_to_device`.

### CI

Every push to `main` and every pull request targeting `main` runs the full test suite on Python 3.12 and 3.13 via the GitHub Actions workflow defined in `.github/workflows/tests.yml`.  Pull requests **must** pass CI before merging.

## Testing and development

### Recommended: Raspberry Pi with Home Assistant OS

For reliable BLE device communication, test on a **Raspberry Pi running Home Assistant OS** or Home Assistant Supervised. The native Bluetooth adapter connects to the Gira device without additional indirection and works out of the box.

Deployment steps:
1. Install Home Assistant OS on your Raspberry Pi ([official guide](https://www.home-assistant.io/installation/)).
2. Copy `custom_components/gira_system_3000` to the HA config directory (e.g. via the Samba or SSH add-on).
3. Restart Home Assistant and add the integration.

### Devcontainer (code editing only)

A devcontainer is provided for local development. It lets you edit the code, run linters, and test the config flow UI.

> **⚠️ BLE device control does not work reliably in the devcontainer on Windows/WSL2.**
> USB-IP Bluetooth passthrough introduces latency that causes BLE connection timeouts when
> connecting to the physical Gira Switch. Code editing, linting, and config flow testing are unaffected.
> See [.devcontainer/README.md](.devcontainer/README.md) for details and a full setup guide.
