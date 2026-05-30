"""Sensor platform for QLD Service Station Prices."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

try:
    from homeassistant.config_entries import ConfigEntry
except ImportError:  # pragma: no cover
    ConfigEntry = Any

try:
    from homeassistant.core import HomeAssistant
except ImportError:  # pragma: no cover
    HomeAssistant = Any

try:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
except ImportError:  # pragma: no cover
    AddEntitiesCallback = Any

from .const import DOMAIN, FUEL_TYPES
from .sensor_best_price import QldFuelBestPriceSensor
from .sensor_common import device_info_for_entry
from .sensor_station import FuelPriceSensor
from .util import get_entry_value, iter_site_fuel_pairs, remove_stale_registry_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the fuel sensors for this specific entry."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    active_unique_ids: set[str] = set()

    is_master = (
        entry.data.get("is_master", False)
        or hass.data[DOMAIN].get("master_entry_id") == entry.entry_id
    )
    chosen_fuels = get_entry_value(entry, FUEL_TYPES, [])

    sites_data = coordinator.data.get("sites", {})
    for site_id, fuel_id in iter_site_fuel_pairs(sites_data, chosen_fuels):
        entity = FuelPriceSensor(coordinator, site_id, fuel_id)
        entities.append(entity)
        active_unique_ids.add(entity._attr_unique_id)

    if is_master:
        for f_id in chosen_fuels:
            global_entity = QldFuelBestPriceSensor(coordinator, f_id, "global")
            tracked_entity = QldFuelBestPriceSensor(coordinator, f_id, "all_tracked")
            entities.append(global_entity)
            entities.append(tracked_entity)
            active_unique_ids.add(global_entity._attr_unique_id)
            active_unique_ids.add(tracked_entity._attr_unique_id)

    for f_id in chosen_fuels:
        local_entity = QldFuelBestPriceSensor(coordinator, f_id, "local")
        nearby_entity = QldFuelBestPriceSensor(coordinator, f_id, "nearby")
        entities.append(local_entity)
        entities.append(nearby_entity)
        active_unique_ids.add(local_entity._attr_unique_id)
        active_unique_ids.add(nearby_entity._attr_unique_id)

    api_diag = QldFuelLastApiResponseSensor(coordinator)
    entities.append(api_diag)
    active_unique_ids.add(api_diag._attr_unique_id)

    remove_stale_registry_entities(
        hass,
        entry,
        active_unique_ids,
        unique_id_prefix=f"{DOMAIN}_{entry.entry_id}_",
    )
    async_add_entities(entities)


class QldFuelLastApiResponseSensor(CoordinatorEntity, SensorEntity):  # type: ignore[misc]
    """Diagnostic: when the shared Queensland fuel price API last returned fresh data."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "last_api_response"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: Any) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.entry.entry_id}_last_api_response"
        )

    @property
    def device_info(self) -> DeviceInfo:
        return device_info_for_entry(self.coordinator.entry)

    @property
    def native_value(self) -> datetime | None:
        domain_data = self.hass.data.get(DOMAIN, {})
        ts = domain_data.get("last_fetch_time")
        return ts if isinstance(ts, datetime) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "last_update_success": self.coordinator.last_update_success,
        }
