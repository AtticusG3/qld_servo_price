"""Best-price summary sensors (global, local, nearby, all tracked)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, RADIUS, ZONE
from .sensor_common import (
    device_info_for_entry,
    device_info_statewide,
    find_all_tracked_best,
    get_fuel_data,
    resolve_location_source,
    station_site_attrs,
)
from .util import fuel_label_for_id, get_entry_value

ScopeKey = Literal["global", "all_tracked", "nearby", "local"]


def _rounded_price(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def _nearby_context_attrs(entity: "QldFuelBestPriceSensor") -> dict[str, Any]:
    return {
        "search_radius_km": float(get_entry_value(entity.coordinator.entry, RADIUS, 5)),
        "source_tracker": resolve_location_source(entity.coordinator.entry),
    }


@dataclass(frozen=True)
class _BestPriceScope:
    """Per-scope configuration for QldFuelBestPriceSensor."""

    scope_key: ScopeKey
    translation_key: str
    is_statewide_device: bool
    entity_category: EntityCategory | None
    enabled_by_default: bool
    station_cheapest_key: str | None
    uses_all_tracked: bool
    refresh_placeholders_on_update: bool

    def build_unique_id(self, coordinator: Any, fuel_id: str) -> str:
        if self.scope_key == "global":
            return f"{DOMAIN}_global_{fuel_id}"
        if self.scope_key == "all_tracked":
            return f"{DOMAIN}_tracked_{fuel_id}"
        if self.scope_key == "nearby":
            return f"{DOMAIN}_nearby_{coordinator.entry.entry_id}_{fuel_id}"
        return f"{DOMAIN}_local_{coordinator.entry.entry_id}_{fuel_id}"

    def build_translation_placeholders(
        self, coordinator: Any, fuel_id: str
    ) -> dict[str, str]:
        fuel_label = fuel_label_for_id(fuel_id)
        if self.scope_key != "local":
            return {"fuel_type": fuel_label}
        zone_id = get_entry_value(coordinator.entry, ZONE, "zone.home")
        state = coordinator.hass.states.get(zone_id)
        zone_name = state.name if state else "Home"
        return {"fuel_type": fuel_label, "zone": zone_name}

    def _all_tracked_snapshot(
        self, entity: "QldFuelBestPriceSensor"
    ) -> tuple[float | None, dict[str, Any] | None]:
        if entity._cached_all_tracked is None:
            entity._cached_all_tracked = find_all_tracked_best(entity.hass, entity.fuel_id)
        return entity._cached_all_tracked

    def get_station_data(self, entity: "QldFuelBestPriceSensor") -> dict[str, Any] | None:
        if self.uses_all_tracked:
            return self._all_tracked_snapshot(entity)[1]
        if self.station_cheapest_key:
            return get_fuel_data(
                entity.coordinator.data.get(self.station_cheapest_key), entity.fuel_id
            )
        return None

    def get_native_value(self, entity: "QldFuelBestPriceSensor") -> float | None:
        if self.uses_all_tracked:
            best_price, _ = self._all_tracked_snapshot(entity)
            return round(float(best_price), 1) if best_price is not None else None
        station_data = self.get_station_data(entity)
        return _rounded_price(station_data.get("price")) if station_data else None

    def empty_attrs(self, entity: "QldFuelBestPriceSensor") -> dict[str, Any]:
        if self.scope_key == "nearby":
            return {
                "fuel_id": entity.fuel_id,
                **_nearby_context_attrs(entity),
                "reason": "no_stations_in_range",
            }
        return {"status": f"No data for fuel_id {entity.fuel_id} in {self.scope_key}"}

    def enrich_attrs(
        self,
        entity: "QldFuelBestPriceSensor",
        base: dict[str, Any],
        station_data: dict[str, Any],
    ) -> dict[str, Any]:
        if self.scope_key != "nearby":
            return base
        base.update(_nearby_context_attrs(entity))
        base["station_entity_id"] = entity._find_station_entity_id(station_data)
        base["reason"] = "ok"
        return base


_SCOPES: dict[str, _BestPriceScope] = {
    "global": _BestPriceScope(
        scope_key="global",
        translation_key="best_price_global",
        is_statewide_device=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_by_default=False,
        station_cheapest_key="global_cheapest",
        uses_all_tracked=False,
        refresh_placeholders_on_update=False,
    ),
    "all_tracked": _BestPriceScope(
        scope_key="all_tracked",
        translation_key="best_price_all_tracked",
        is_statewide_device=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_by_default=False,
        station_cheapest_key=None,
        uses_all_tracked=True,
        refresh_placeholders_on_update=False,
    ),
    "nearby": _BestPriceScope(
        scope_key="nearby",
        translation_key="best_price_nearby",
        is_statewide_device=False,
        entity_category=None,
        enabled_by_default=True,
        station_cheapest_key="local_cheapest",
        uses_all_tracked=False,
        refresh_placeholders_on_update=False,
    ),
    "local": _BestPriceScope(
        scope_key="local",
        translation_key="best_price_local",
        is_statewide_device=False,
        entity_category=None,
        enabled_by_default=False,
        station_cheapest_key="local_cheapest",
        uses_all_tracked=False,
        refresh_placeholders_on_update=True,
    ),
}


class QldFuelBestPriceSensor(CoordinatorEntity, SensorEntity):  # type: ignore[misc]
    """Sensor for reporting best prices (Global, Local, or All Tracked)."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "¢/L"
    _attr_device_class = None
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: Any, fuel_id: str, scope: str) -> None:
        super().__init__(coordinator)
        self.fuel_id = fuel_id
        self._scope_config = _SCOPES[scope]
        self._cached_all_tracked: tuple[float | None, dict[str, Any] | None] | None = None

        self._attr_unique_id = self._scope_config.build_unique_id(coordinator, fuel_id)
        self._attr_translation_key = self._scope_config.translation_key
        self._attr_translation_placeholders = self._scope_config.build_translation_placeholders(
            coordinator, fuel_id
        )
        self._attr_entity_category = self._scope_config.entity_category
        self._attr_entity_registry_enabled_default = self._scope_config.enabled_by_default

    def _handle_coordinator_update(self) -> None:
        self._cached_all_tracked = None
        if self._scope_config.refresh_placeholders_on_update:
            self._attr_translation_placeholders = self._scope_config.build_translation_placeholders(
                self.coordinator, self.fuel_id
            )
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        if self._scope_config.is_statewide_device:
            return device_info_statewide()
        return device_info_for_entry(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        return self._scope_config.get_native_value(self)

    def _find_station_entity_id(self, station_data: dict[str, Any]) -> str | None:
        site_id = station_data.get("site_id")
        if site_id is None:
            return None

        entity_registry = er.async_get(self.hass)
        target_unique_id = (
            f"{DOMAIN}_{self.coordinator.entry.entry_id}_{self.fuel_id}_{site_id}"
        )
        entity_id = entity_registry.async_get_entity_id(
            "sensor",
            DOMAIN,
            target_unique_id,
        )
        return entity_id if isinstance(entity_id, str) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        station_data = self._scope_config.get_station_data(self)
        if not station_data:
            return self._scope_config.empty_attrs(self)

        attrs = station_site_attrs(
            self.coordinator.data, station_data.get("site_id"), station_data
        )
        if "status" in attrs:
            return attrs

        return self._scope_config.enrich_attrs(self, attrs, station_data)
