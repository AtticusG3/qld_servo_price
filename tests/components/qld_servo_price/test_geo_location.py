"""Tests for qld_servo_price geo_location platform."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

pytestmark = pytest.mark.no_fail_on_log_exception


def _install_ha_stubs_for_geo():
    for key in list(sys.modules):
        if key == "homeassistant" or key.startswith("homeassistant."):
            sys.modules.pop(key)

    ha = ModuleType("homeassistant")
    ha.__path__ = []
    sys.modules["homeassistant"] = ha

    ha_components = ModuleType("homeassistant.components")
    ha_components.__path__ = []
    sys.modules["homeassistant.components"] = ha_components

    helpers_pkg = ModuleType("homeassistant.helpers")
    helpers_pkg.__path__ = []
    sys.modules["homeassistant.helpers"] = helpers_pkg

    entity_mod = ModuleType("homeassistant.helpers.entity")

    class _Entity:
        _attr_unique_id: str | None = None

        @property
        def unique_id(self):
            return self._attr_unique_id

    entity_mod.Entity = _Entity
    sys.modules["homeassistant.helpers.entity"] = entity_mod

    geo_comp = ModuleType("homeassistant.components.geo_location")

    class GeolocationEvent(entity_mod.Entity):
        """Stub base for GeolocationEvent."""

    geo_comp.GeolocationEvent = GeolocationEvent
    sys.modules["homeassistant.components.geo_location"] = geo_comp

    helpers_er = ModuleType("homeassistant.helpers.entity_registry")

    def _default_async_entries_for_config_entry(_registry, _entry_id):
        return []

    helpers_er.async_get = lambda _h: SimpleNamespace(
        async_remove=lambda *_a, **_k: None,
    )
    helpers_er.async_entries_for_config_entry = _default_async_entries_for_config_entry
    sys.modules["homeassistant.helpers.entity_registry"] = helpers_er

    dr = ModuleType("homeassistant.helpers.device_registry")
    dr.DeviceEntryType = SimpleNamespace(SERVICE="service")
    dr.DeviceInfo = dict
    sys.modules["homeassistant.helpers.device_registry"] = dr

    platform_mod = ModuleType("homeassistant.helpers.entity_platform")
    platform_mod.AddEntitiesCallback = object
    sys.modules["homeassistant.helpers.entity_platform"] = platform_mod

    uc = ModuleType("homeassistant.helpers.update_coordinator")

    class CoordinatorEntity(entity_mod.Entity):
        def __init__(self, coordinator):
            super().__init__()
            self.coordinator = coordinator

        def _handle_coordinator_update(self):
            return None

    uc.CoordinatorEntity = CoordinatorEntity
    sys.modules["homeassistant.helpers.update_coordinator"] = uc

    ce = ModuleType("homeassistant.config_entries")
    ce.ConfigEntry = object
    sys.modules["homeassistant.config_entries"] = ce

    homeassistant_core = ModuleType("homeassistant.core")
    homeassistant_core.HomeAssistant = object
    sys.modules["homeassistant.core"] = homeassistant_core


def _load_geo_location_module():
    for key in list(sys.modules):
        if key.startswith("custom_components.qld_servo_price"):
            sys.modules.pop(key)

    _install_ha_stubs_for_geo()

    const_mod = ModuleType("custom_components.qld_servo_price.const")
    const_mod.DOMAIN = "qld_servo_price"
    const_mod.ENABLE_GEO_ENTITIES = "enable_geo_entities"
    const_mod.FUEL_TYPES = "fuel_types"
    const_mod.FUEL_TYPES_OPTIONS = [{"value": "12", "label": "E10"}]
    const_mod.GEO_LOCATION_SOURCE = "qld_servo_price"
    const_mod.LOCATION_ENTITY = "location_entity"
    sys.modules["custom_components.qld_servo_price.const"] = const_mod

    util_mod = ModuleType("custom_components.qld_servo_price.util")

    def get_entry_value(entry, key, default=None):
        return entry.options.get(key, entry.data.get(key, default))

    def iter_site_fuel_pairs(sites_data, chosen_fuels):
        allowed = {str(fid) for fid in chosen_fuels}
        for site_id, site_data in sites_data.items():
            for price_info in site_data.get("prices", []):
                fuel_id = str(price_info.get("FuelId"))
                if fuel_id in allowed:
                    yield str(site_id), fuel_id

    def remove_stale_registry_entities(hass, entry, active_unique_ids, unique_id_prefix):
        registry = sys.modules["homeassistant.helpers.entity_registry"].async_get(hass)
        for registry_entry in sys.modules[
            "homeassistant.helpers.entity_registry"
        ].async_entries_for_config_entry(registry, entry.entry_id):
            unique_id = getattr(registry_entry, "unique_id", None)
            if not unique_id or not unique_id.startswith(unique_id_prefix):
                continue
            if unique_id not in active_unique_ids:
                registry.async_remove(registry_entry.entity_id)

    def site_price_for_fuel(site_data, fuel_id):
        for price_info in site_data.get("prices", []):
            if str(price_info.get("FuelId")) == str(fuel_id):
                return price_info.get("Price")
        return None

    def fuel_label_for_id(fuel_id):
        if str(fuel_id) == "12":
            return "E10"
        return str(fuel_id)

    util_mod.get_entry_value = get_entry_value
    util_mod.iter_site_fuel_pairs = iter_site_fuel_pairs
    util_mod.remove_stale_registry_entities = remove_stale_registry_entities
    util_mod.site_price_for_fuel = site_price_for_fuel
    util_mod.fuel_label_for_id = fuel_label_for_id
    sys.modules["custom_components.qld_servo_price.util"] = util_mod

    pkg = ModuleType("custom_components.qld_servo_price")
    pkg.__path__ = []
    sys.modules["custom_components.qld_servo_price"] = pkg

    integration_root = (
        Path(__file__).resolve().parents[3]
        / "custom_components"
        / "qld_servo_price"
    )

    common_path = integration_root / "sensor_common.py"
    common_spec = importlib.util.spec_from_file_location(
        "custom_components.qld_servo_price.sensor_common",
        str(common_path),
    )
    common_mod = importlib.util.module_from_spec(common_spec)
    assert common_spec and common_spec.loader
    sys.modules["custom_components.qld_servo_price.sensor_common"] = common_mod
    common_spec.loader.exec_module(common_mod)

    path = integration_root / "geo_location.py"
    spec = importlib.util.spec_from_file_location(
        "custom_components.qld_servo_price.geo_location",
        str(path),
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["custom_components.qld_servo_price.geo_location"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_geo_entities_enabled_uses_options_and_data():
    mod = _load_geo_location_module()
    entry = SimpleNamespace(options={}, data={})
    assert mod.geo_entities_enabled(entry) is False
    entry.options = {"enable_geo_entities": True}
    assert mod.geo_entities_enabled(entry) is True
    entry.options = {}
    entry.data = {"enable_geo_entities": True}
    assert mod.geo_entities_enabled(entry) is True


def test_station_geo_event_placeholders_and_unique_id():
    mod = _load_geo_location_module()
    entry = SimpleNamespace(entry_id="e1", options={}, data={})
    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=entry,
        data={
            "sites": {
                "99": {
                    "name": "Station A",
                    "latitude": -27.4,
                    "longitude": 153.0,
                    "distance": 3.3,
                    "prices": [{"FuelId": "12", "Price": 200.5}],
                },
            },
            "local_cheapest": {
                "12": {"price": 195.0},
            },
        },
    )
    entity = mod.QldFuelStationGeoEvent(coord, "99", "12")
    assert entity.unique_id == "qld_servo_price_geo_e1_12_99"
    ph = entity._attr_translation_placeholders
    assert ph["price"] == "200.5"
    assert ph["fuel_type"] == "E10"
    assert ph["station"] == "Station A"
    assert entity.latitude == pytest.approx(-27.4)
    assert entity.distance == pytest.approx(3.3)
    attrs = entity.extra_state_attributes
    assert attrs["price"] == 200.5
    assert attrs["cheapest_price_in_zone"] == 195.0


def test_async_setup_entry_disabled_removes_stale_geo_entities():
    mod = _load_geo_location_module()
    removed: list[str] = []

    fake_reg = SimpleNamespace(
        entity_id="geo_location.old_station",
        unique_id="qld_servo_price_geo_entry1_12_99",
    )

    er_mod = sys.modules["homeassistant.helpers.entity_registry"]

    def async_get(_hass):
        return SimpleNamespace(
            async_remove=lambda eid: removed.append(eid),
        )

    er_mod.async_get = async_get
    er_mod.async_entries_for_config_entry = (
        lambda _reg, eid: [fake_reg] if eid == "entry1" else []
    )

    entry = SimpleNamespace(
        entry_id="entry1",
        options={},
        data={},
        runtime_data=SimpleNamespace(data={"sites": {}}),
    )
    hass = SimpleNamespace()

    async def run():
        await mod.async_setup_entry(hass, entry, lambda _e, _u=False: None)

    asyncio.run(run())
    assert removed == ["geo_location.old_station"]


def test_async_setup_entry_enabled_adds_entities():
    mod = _load_geo_location_module()
    er_mod = sys.modules["homeassistant.helpers.entity_registry"]
    er_mod.async_get = lambda _h: SimpleNamespace(
        async_entries_for_config_entry=lambda *_a, **_k: [],
        async_remove=lambda *_a, **_k: None,
    )

    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=SimpleNamespace(
            entry_id="e2",
            options={"fuel_types": ["12"], "enable_geo_entities": True},
            data={},
        ),
        data={
            "sites": {
                "1": {
                    "name": "S",
                    "latitude": -27.0,
                    "longitude": 153.0,
                    "distance": 1.0,
                    "prices": [{"FuelId": "12", "Price": 180.0}],
                },
            },
            "local_cheapest": {"12": {"price": 180.0}},
        },
    )
    entry = SimpleNamespace(
        entry_id="e2",
        options={"fuel_types": ["12"], "enable_geo_entities": True},
        data={},
        runtime_data=coord,
    )
    hass = SimpleNamespace()
    added = []

    async def run():
        await mod.async_setup_entry(
            hass,
            entry,
            lambda ents, _update=False: added.extend(ents),
        )

    asyncio.run(run())
    assert len(added) == 1
    assert added[0].unique_id == "qld_servo_price_geo_e2_12_1"


def test_remove_stale_geo_entities_branches():
    mod = _load_geo_location_module()
    removed: list[str] = []

    stale = SimpleNamespace(
        entity_id="geo.stale",
        unique_id="qld_servo_price_geo_entry1_12_99",
    )
    other_entry_prefix = SimpleNamespace(
        entity_id="geo.other",
        unique_id="qld_servo_price_geo_other_12_1",
    )
    no_uid = SimpleNamespace(entity_id="geo.non", unique_id=None)
    wrong_prefix = SimpleNamespace(
        entity_id="geo.wp",
        unique_id="sensor_entry1_x",
    )

    er_mod = sys.modules["homeassistant.helpers.entity_registry"]

    def async_get(_hass):
        return SimpleNamespace(
            async_remove=lambda eid: removed.append(eid),
        )

    er_mod.async_get = async_get
    er_mod.async_entries_for_config_entry = lambda _reg, eid: (
        [stale, other_entry_prefix, no_uid, wrong_prefix] if eid == "entry1" else []
    )

    mod._remove_stale_geo_entities(
        SimpleNamespace(),
        SimpleNamespace(entry_id="entry1"),
        {"qld_servo_price_geo_entry1_12_1"},
    )
    assert removed == ["geo.stale"]


def test_async_setup_entry_skips_empty_prices_and_unlisted_fuels():
    mod = _load_geo_location_module()
    er_mod = sys.modules["homeassistant.helpers.entity_registry"]
    er_mod.async_get = lambda _h: SimpleNamespace(
        async_entries_for_config_entry=lambda *_a, **_k: [],
        async_remove=lambda *_a, **_k: None,
    )

    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=SimpleNamespace(
            entry_id="e3",
            options={"fuel_types": ["12"], "enable_geo_entities": True},
            data={},
        ),
        data={
            "sites": {
                "1": {"name": "NoPrices", "prices": []},
                "2": {
                    "name": "WrongFuel",
                    "latitude": -27.0,
                    "longitude": 153.0,
                    "distance": 1.0,
                    "prices": [{"FuelId": "5", "Price": 100.0}],
                },
            },
        },
    )
    entry = SimpleNamespace(
        entry_id="e3",
        options={"fuel_types": ["12"], "enable_geo_entities": True},
        data={},
        runtime_data=coord,
    )
    added: list = []

    async def run():
        await mod.async_setup_entry(
            SimpleNamespace(),
            entry,
            lambda ents, _update=False: added.extend(ents),
        )

    asyncio.run(run())
    assert added == []


def test_station_geo_event_invalid_price_placeholder_and_coordinates():
    mod = _load_geo_location_module()
    entry = SimpleNamespace(entry_id="e4", options={}, data={})
    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=entry,
        data={
            "sites": {
                "1": {
                    "name": "S",
                    "latitude": "not-a-float",
                    "longitude": None,
                    "distance": "x",
                    "prices": [{"FuelId": "12", "Price": "bad"}],
                },
            },
            "local_cheapest": {},
        },
    )
    entity = mod.QldFuelStationGeoEvent(coord, "1", "12")
    assert entity._attr_translation_placeholders["price"] == "?"
    assert entity.latitude is None
    assert entity.longitude is None
    assert entity.distance is None


def test_station_geo_event_unknown_fuel_uses_default_icon():
    mod = _load_geo_location_module()
    entry = SimpleNamespace(entry_id="e5", options={}, data={})
    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=entry,
        data={
            "sites": {
                "1": {
                    "name": "S",
                    "latitude": -27.0,
                    "longitude": 153.0,
                    "distance": 2.0,
                    "prices": [{"FuelId": "99", "Price": 150.0}],
                },
            },
            "local_cheapest": {},
        },
    )
    entity = mod.QldFuelStationGeoEvent(coord, "1", "99")
    assert entity._attr_icon == "mdi:gas-station"


def test_station_geo_event_extra_attributes_delta_skips_on_bad_numbers():
    mod = _load_geo_location_module()
    entry = SimpleNamespace(entry_id="e6", options={}, data={})
    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=entry,
        data={
            "sites": {
                "1": {
                    "name": "S",
                    "address": "1 St",
                    "postcode": "4000",
                    "latitude": -27.0,
                    "longitude": 153.0,
                    "distance": 1.0,
                    "prices": [{"FuelId": "12", "Price": 200.0}],
                },
            },
            "local_cheapest": {"12": {"price": 200.0}},
        },
    )
    entity = mod.QldFuelStationGeoEvent(coord, "1", "12")
    attrs = entity.extra_state_attributes
    assert attrs.get("price_delta_to_cheapest_in_zone") == 0.0
    assert attrs["cheapest_price_in_zone"] == 200.0

    coord2 = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=entry,
        data={
            "sites": {
                "1": {
                    "name": "S",
                    "address": "1 St",
                    "postcode": "4000",
                    "latitude": -27.0,
                    "longitude": 153.0,
                    "distance": 1.0,
                    "prices": [{"FuelId": "12", "Price": 200.0}],
                },
            },
            "local_cheapest": {"12": {"price": object()}},
        },
    )
    entity2 = mod.QldFuelStationGeoEvent(coord2, "1", "12")
    attrs2 = entity2.extra_state_attributes
    assert "price_delta_to_cheapest_in_zone" not in attrs2
    assert "cheapest_price_in_zone" in attrs2


def test_station_geo_event_longitude_distance_invalid_and_unit():
    mod = _load_geo_location_module()
    entry = SimpleNamespace(entry_id="e8", options={}, data={})
    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=entry,
        data={
            "sites": {
                "1": {
                    "name": "S",
                    "latitude": -27.0,
                    "longitude": "nope",
                    "distance": {},
                    "prices": [{"FuelId": "12", "Price": 1.0}],
                },
            },
            "local_cheapest": {},
        },
    )
    entity = mod.QldFuelStationGeoEvent(coord, "1", "12")
    assert entity.longitude is None
    assert entity.distance is None
    assert entity.unit_of_measurement == mod.DEFAULT_DISTANCE_UNIT


def test_station_geo_event_device_info_and_coordinator_update_hook():
    mod = _load_geo_location_module()
    entry = SimpleNamespace(entry_id="e7", title="Fuel near X", options={}, data={})
    coord = SimpleNamespace(
        hass=SimpleNamespace(),
        entry=entry,
        data={
            "sites": {
                "1": {
                    "name": "Renamed",
                    "latitude": -27.0,
                    "longitude": 153.0,
                    "distance": 1.0,
                    "prices": [{"FuelId": "12", "Price": 180.0}],
                },
            },
            "local_cheapest": {"12": {"price": 175.0}},
        },
    )
    entity = mod.QldFuelStationGeoEvent(coord, "1", "12")
    di = entity.device_info
    assert di["name"] == "Fuel near X"
    coord.data["sites"]["1"]["name"] = "NewName"
    entity._handle_coordinator_update()
    assert entity._attr_translation_placeholders["station"] == "NewName"
