# General instructions for the repository

This repository contains custom components for Home Assistant, specifically for the Gira System 3000. The code is organized into different files based on the type of entity (e.g., cover, light, sensor). Each file contains the necessary logic to integrate the respective entities with Home Assistant.

When contributing to this repository, please ensure that your code follows the existing style and conventions. This includes using appropriate logging, defining configuration schemas where necessary, and adhering to Home Assistant's best practices for custom components.

## Language and Style

- Use english for all code comments and documentation
- Refer to Home Assistant's developer documentation for guidance on best practices and coding standards: https://developers.home-assistant.io/docs/creating_component_index

## Deployment

The custom components in this reposiory can be deployed to a Home Assistant instance using HACS (Home Assistant Community Store).
Please respect the HACS guidelines for custom components when making contributions: https://hacs.xyz/docs/publish/

## Local testing

The project contains a devcontainer for running a containerized instance of Home Assistant.

## Automated tests

The repository contains a pytest-based test suite in the `tests/` directory.  All tests run without physical Bluetooth hardware.

### Running the tests

```bash
pip install -r requirements_test.txt
pytest tests/ -v
```

### Test structure

- `tests/conftest.py` – shared fixtures; extends `custom_components.__path__` so HA's integration loader can discover the integration during tests.
- `tests/test_api.py` – pure-function tests for BLE command bytes and the send-command queue.
- `tests/test_coordinator.py` – tests for `GiraBleCoordinator` delegation and sensor-frame parsing.
- `tests/test_cover.py` – tests for `GiraBleCover` entity state and the Gira position inversion logic.
- `tests/test_config_flow.py` – tests for both the user-initiated and Bluetooth auto-discovery config flows.

### Writing tests for new features

1. **Add tests alongside your code change** – every new public method or behaviour should have at least one test.
2. **Mock hardware** – use `unittest.mock.patch` and `MagicMock` instead of real BLE connections.
   - Patch `asyncio.create_task` (with `return_value=MagicMock()`) when instantiating `GiraBleApi` in synchronous tests to suppress the background executor coroutine.
   - Patch `homeassistant.components.bluetooth.async_discovered_service_info` in config-flow tests that call `async_step_user`.
3. **Config flow tests** require both `mock_bluetooth_dependencies` and `enable_custom_integrations` fixtures so that HA can find and load the integration without real hardware.
4. **Keep tests independent** – each test function must set up its own state; do not rely on test ordering.
5. **Check CI** – every pull request must pass the GitHub Actions workflow (`.github/workflows/tests.yml`) before merging.

### CI workflow

The workflow (`.github/workflows/tests.yml`) runs on every push to `main` and on every pull request targeting `main`.  It executes the full test suite on Python 3.12 and 3.13.
