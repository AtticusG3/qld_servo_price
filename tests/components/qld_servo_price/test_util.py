"""Tests for shared utility helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

pytestmark = pytest.mark.no_fail_on_log_exception


def _load_util_module():
    for key in list(sys.modules):
        if key.startswith("custom_components.qld_servo_price"):
            sys.modules.pop(key)

    homeassistant = sys.modules.get("homeassistant")
    if homeassistant is None:
        homeassistant = ModuleType("homeassistant")
        homeassistant.__path__ = []
        sys.modules["homeassistant"] = homeassistant

    helpers = sys.modules.get("homeassistant.helpers")
    if helpers is None:
        helpers = ModuleType("homeassistant.helpers")
        helpers.__path__ = []
        sys.modules["homeassistant.helpers"] = helpers

    entity_registry = ModuleType("homeassistant.helpers.entity_registry")

    entity_registry.async_get = lambda _hass: SimpleNamespace(
        async_remove=lambda _entity_id: None
    )
    entity_registry.async_entries_for_config_entry = lambda *_a, **_k: []
    sys.modules["homeassistant.helpers.entity_registry"] = entity_registry
    setattr(homeassistant, "helpers", helpers)

    util_module = sys.modules.get("homeassistant.util")
    if util_module is None:
        util_module = ModuleType("homeassistant.util")
        util_module.__path__ = []
        sys.modules["homeassistant.util"] = util_module
    setattr(homeassistant, "util", util_module)

    const_module = ModuleType("custom_components.qld_servo_price.const")
    const_module.FUEL_TYPES_OPTIONS = [{"value": "12", "label": "E10"}]
    const_module.LOCATION_ENTITY = "location_entity"
    const_module.ZONE = "zone"
    sys.modules["custom_components.qld_servo_price.const"] = const_module

    package = ModuleType("custom_components.qld_servo_price")
    package.__path__ = []
    sys.modules["custom_components.qld_servo_price"] = package

    path = Path(__file__).resolve().parents[3] / "custom_components" / "qld_servo_price" / "util.py"
    spec = importlib.util.spec_from_file_location(
        "custom_components.qld_servo_price.util",
        str(path),
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["custom_components.qld_servo_price.util"] = module
    spec.loader.exec_module(module)
    return module


def test_coords_from_state_branches():
    module = _load_util_module()
    assert module.coords_from_state(None) == (None, None)
    assert module.coords_from_state(SimpleNamespace(attributes={})) == (None, None)
    assert module.coords_from_state(
        SimpleNamespace(attributes={"latitude": "bad", "longitude": 153.0})
    ) == (None, None)
    assert module.coords_from_state(
        SimpleNamespace(attributes={"latitude": "-27.5", "longitude": "153.0"})
    ) == (-27.5, 153.0)


def test_get_entry_value_prefers_options_and_supports_default():
    module = _load_util_module()
    entry = SimpleNamespace(options={"zone": "zone.work"}, data={"zone": "zone.home"})
    assert module.get_entry_value(entry, "zone") == "zone.work"
    assert module.get_entry_value(entry, "missing") is None
    assert module.get_entry_value(entry, "missing", "fallback") == "fallback"


def test_iter_site_fuel_pairs_filters_and_yields_expected_pairs():
    module = _load_util_module()
    sites_data = {
        "1": {"prices": [{"FuelId": "12", "Price": 100}, {"FuelId": "5", "Price": 110}]},
        "2": {"prices": []},
        "3": {"prices": [{"FuelId": 12, "Price": 90}]},
    }
    pairs = list(module.iter_site_fuel_pairs(sites_data, ["12"]))
    assert pairs == [("1", "12"), ("3", "12")]


def test_remove_stale_registry_entities_removes_only_stale_matching_prefix():
    module = _load_util_module()
    removed = []
    registry = SimpleNamespace(async_remove=lambda entity_id: removed.append(entity_id))
    entries = [
        SimpleNamespace(entity_id="sensor.keep", unique_id="qld_prefix_keep"),
        SimpleNamespace(entity_id="sensor.stale", unique_id="qld_prefix_stale"),
        SimpleNamespace(entity_id="sensor.other", unique_id="other_prefix_stale"),
    ]
    entity_registry = sys.modules["homeassistant.helpers.entity_registry"]
    entity_registry.async_get = lambda _hass: registry
    entity_registry.async_entries_for_config_entry = lambda _reg, _entry_id: entries

    module.remove_stale_registry_entities(
        hass=SimpleNamespace(),
        entry=SimpleNamespace(entry_id="entry1"),
        active_unique_ids={"qld_prefix_keep"},
        unique_id_prefix="qld_prefix_",
    )
    assert removed == ["sensor.stale"]


def test_resolve_location_from_input_branches():
    module = _load_util_module()
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: None))
    errors: dict[str, str] = {}
    assert module.resolve_location_from_input(
        hass, {"location_entity": "person.missing", "zone": "zone.missing"}, errors
    ) == (None, None, None)
    assert errors["location_entity"] == "location_entity_not_found"
    assert errors["zone"] == "zone_not_found"


def test_site_price_for_fuel_and_fuel_label_helpers():
    module = _load_util_module()
    site = {"prices": [{"FuelId": "12", "Price": 200.5}]}
    assert module.site_price_for_fuel(site, "12") == 200.5
    assert module.site_price_for_fuel(site, "5") is None
    assert module.fuel_label_for_id("12") == "E10"
    assert module.fuel_label_for_id("99") == "99"
