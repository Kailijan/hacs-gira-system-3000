"""Global fixtures and configuration for Gira System 3000 tests."""
import pathlib

import pytest
from homeassistant.core import HomeAssistant

# ---------------------------------------------------------------------------
# Ensure HA's integration loader can discover our custom component.
# The pytest-homeassistant-custom-component package uses a testing_config
# directory whose custom_components package has an __init__.py, making it a
# regular (non-namespace) package that shadows our directory.  Appending our
# path here makes it visible to HA's _get_custom_components() scanner.
# ---------------------------------------------------------------------------
import custom_components as _cc

_OUR_CC_PATH = str(pathlib.Path(__file__).parent.parent / "custom_components")
if _OUR_CC_PATH not in list(_cc.__path__):
    _cc.__path__.append(_OUR_CC_PATH)

# Register the pytest-homeassistant-custom-component plugin, which provides
# the `hass` fixture and other Home Assistant test utilities.
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_bluetooth_dependencies(hass: HomeAssistant) -> None:
    """Pre-mark Bluetooth HA components as already set up.

    This prevents async_process_deps_reqs from trying to load the real
    'bluetooth' and 'bluetooth_adapters' HA components (which require the
    'usb' component and pyudev, unavailable in CI) when the config flow is
    initialised with enable_custom_integrations.
    """
    hass.config.components.add("bluetooth")
    hass.config.components.add("bluetooth_adapters")
