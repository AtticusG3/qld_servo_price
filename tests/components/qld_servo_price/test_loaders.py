"""Shared module loaders for qld_servo_price unit tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

_UTIL_MODULE_NAME = "custom_components.qld_servo_price.util"
_INTEGRATION_UTIL_PATH = (
    Path(__file__).resolve().parents[3]
    / "custom_components"
    / "qld_servo_price"
    / "util.py"
)


def _ensure_entity_registry_stub() -> None:
    """Install a minimal entity_registry stub if not already present."""
    er_key = "homeassistant.helpers.entity_registry"
    if er_key in sys.modules:
        return

    ha = sys.modules.get("homeassistant")
    if ha is None:
        ha = ModuleType("homeassistant")
        ha.__path__ = []
        sys.modules["homeassistant"] = ha

    helpers = sys.modules.get("homeassistant.helpers")
    if helpers is None:
        helpers = ModuleType("homeassistant.helpers")
        helpers.__path__ = []
        sys.modules["homeassistant.helpers"] = helpers
        setattr(ha, "helpers", helpers)

    entity_registry = ModuleType(er_key)
    entity_registry.async_get = lambda _hass: SimpleNamespace(
        async_remove=lambda *_a, **_k: None,
    )
    entity_registry.async_entries_for_config_entry = lambda *_a, **_k: []
    sys.modules[er_key] = entity_registry


def register_real_util_module() -> ModuleType:
    """Load and register the real integration util.py in sys.modules."""
    const_key = "custom_components.qld_servo_price.const"
    if const_key not in sys.modules:
        raise RuntimeError(
            f"{const_key} must be registered before register_real_util_module()"
        )

    _ensure_entity_registry_stub()

    package_key = "custom_components.qld_servo_price"
    if package_key not in sys.modules:
        package = ModuleType(package_key)
        package.__path__ = []
        sys.modules[package_key] = package

    spec = importlib.util.spec_from_file_location(
        _UTIL_MODULE_NAME,
        str(_INTEGRATION_UTIL_PATH),
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[_UTIL_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module
