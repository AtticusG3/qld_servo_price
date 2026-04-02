"""Map-oriented geolocation entities for in-range station fuel prices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

try:
    from homeassistant.config_entries import ConfigEntry
except ImportError:  # pragma: no cover
    ConfigEntry = Any

try:
    from homeassistant.core import HomeAssistant
except ImportError:  # pragma: no cover
    HomeAssistant = Any

from .const import (
    DOMAIN,
    ENABLE_GEO_ENTITIES,
    FUEL_TYPES,
    FUEL_TYPES_OPTIONS,
    GEO_LOCATION_SOURCE,
)
from .sensor import get_fuel_data

PARALLEL_UPDATES = 1

DEFAULT_DISTANCE_UNIT = "km"

FUEL_ID_TO_ICON: dict[str, str] = {
    "12": "mdi:gas-station",  # E10
    "2": "mdi:gas-station-outline",
    "5": "mdi:gas-station",
    "8": "mdi:fire",
    "3": "mdi:barrel",
    "14": "mdi:barrel-outline",
    "4": "mdi:propane-tank",
    "19": "mdi:leaf",
}


def geo_entities_enabled(entry: ConfigEntry) -> bool:
    """Return True when map geo entities are enabled for this config entry."""
    return bool(
        entry.options.get(ENABLE_GEO_ENTITIES, entry.data.get(ENABLE_GEO_ENTITIES, False))
    )


def _remove_stale_geo_entities(
    hass: HomeAssistant, entry: ConfigEntry, active_unique_ids: set[str]
) -> None:
    """Remove geo_location registry entries for this config entry that are no longer active."""
    entity_registry = er.async_get(hass)
    prefix = f"{DOMAIN}_geo_{entry.entry_id}_"
    for registry_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        unique_id = getattr(registry_entry, "unique_id", None)
        if not unique_id or not unique_id.startswith(prefix):
            continue
        if unique_id not in active_unique_ids:
            entity_registry.async_remove(registry_entry.entity_id)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up geolocation entities when enabled."""
    coordinator = entry.runtime_data

    if not geo_entities_enabled(entry):
        _remove_stale_geo_entities(hass, entry, set())
        return

    chosen_fuels = entry.options.get(FUEL_TYPES, entry.data.get(FUEL_TYPES, []))
    sites_data = coordinator.data.get("sites", {})

    entities: list[QldFuelStationGeoEvent] = []
    active_unique_ids: set[str] = set()

    for site_id, site_data in sites_data.items():
        if not site_data.get("prices"):
            continue
        for price_info in site_data["prices"]:
            f_id = str(price_info.get("FuelId"))
            if f_id not in chosen_fuels:
                continue
            entity = QldFuelStationGeoEvent(coordinator, site_id, f_id)
            entities.append(entity)
            active_unique_ids.add(entity.unique_id)

    _remove_stale_geo_entities(hass, entry, active_unique_ids)
    async_add_entities(entities)


class QldFuelStationGeoEvent(CoordinatorEntity, GeolocationEvent):  # type: ignore[misc]
    """Geolocation pin for one station fuel price (Map geo_location_sources)."""

    _attr_has_entity_name = True
    _attr_translation_key = "station_map_pin"
    _attr_source = GEO_LOCATION_SOURCE

    def __init__(self, coordinator: Any, site_id: str, fuel_id: str) -> None:
        super().__init__(coordinator)
        self.site_id = site_id
        self.fuel_id = fuel_id
        self._attr_unique_id = f"{DOMAIN}_geo_{coordinator.entry.entry_id}_{fuel_id}_{site_id}"
        self._attr_icon = FUEL_ID_TO_ICON.get(fuel_id, "mdi:gas-station")
        self._sync_map_pin_placeholders()

    def _sync_map_pin_placeholders(self) -> None:
        site = self.coordinator.data.get("sites", {}).get(self.site_id, {})
        fuel_info = next(
            (f for f in FUEL_TYPES_OPTIONS if f["value"] == self.fuel_id),
            {"label": self.fuel_id},
        )
        site_name = site.get("name") or "Unknown"
        price = None
        for p in site.get("prices", []):
            if str(p.get("FuelId")) == self.fuel_id:
                price = p.get("Price")
                break
        price_text = "?"
        if price is not None:
            try:
                price_text = f"{float(price):.1f}"
            except (TypeError, ValueError):
                price_text = "?"
        self._attr_translation_placeholders = {
            "fuel_type": str(fuel_info["label"]),
            "price": price_text,
            "station": site_name,
        }

    def _handle_coordinator_update(self) -> None:
        self._sync_map_pin_placeholders()
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"zone_{self.coordinator.entry.entry_id}")},
            name=self.coordinator.entry.title,
            manufacturer="Queensland fuel price API",
            model="Local Zone Monitor",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def latitude(self) -> float | None:
        """Return latitude (overridden so coordinator updates are not cached stale)."""
        site = self.coordinator.data.get("sites", {}).get(self.site_id, {})
        lat = site.get("latitude")
        try:
            return float(lat) if lat is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def longitude(self) -> float | None:
        """Return longitude (overridden so coordinator updates are not cached stale)."""
        site = self.coordinator.data.get("sites", {}).get(self.site_id, {})
        lon = site.get("longitude")
        try:
            return float(lon) if lon is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def distance(self) -> float | None:
        """Return distance in km (overridden so coordinator updates are not cached stale)."""
        site = self.coordinator.data.get("sites", {}).get(self.site_id, {})
        d = site.get("distance")
        try:
            return float(d) if d is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def unit_of_measurement(self) -> str:
        return DEFAULT_DISTANCE_UNIT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        site = self.coordinator.data.get("sites", {}).get(self.site_id, {})
        fuel_info = next(
            (f for f in FUEL_TYPES_OPTIONS if f["value"] == self.fuel_id),
            {"label": self.fuel_id},
        )
        price = None
        for p in site.get("prices", []):
            if str(p.get("FuelId")) == self.fuel_id:
                price = p.get("Price")
                break

        cheapest = get_fuel_data(
            self.coordinator.data.get("local_cheapest"), self.fuel_id
        )
        cheapest_price = cheapest.get("price") if cheapest else None

        attrs: dict[str, Any] = {
            "fuel_id": self.fuel_id,
            "fuel_label": fuel_info["label"],
            "station_name": site.get("name"),
            "address": f"{site.get('address', '')} {site.get('postcode', '')}".strip(),
        }
        if price is not None:
            attrs["price"] = price
        if cheapest_price is not None and price is not None:
            try:
                attrs["price_delta_to_cheapest_in_zone"] = round(
                    float(price) - float(cheapest_price), 1
                )
            except (TypeError, ValueError):
                pass
            attrs["cheapest_price_in_zone"] = cheapest_price

        return attrs
