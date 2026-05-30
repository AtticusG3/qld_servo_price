"""Shared utility helpers for qld_servo_price integration modules."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from homeassistant.helpers import entity_registry as er

from .const import FUEL_TYPES_OPTIONS, LOCATION_ENTITY, ZONE

_MISSING = object()


def coords_from_state(state: Any) -> tuple[float | None, float | None]:
    """Extract and normalize latitude/longitude from an entity state."""
    if not state:
        return None, None

    lat = state.attributes.get("latitude")
    lon = state.attributes.get("longitude")
    if lat is None or lon is None:
        return None, None

    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None


def get_entry_value(entry: Any, key: str, default: Any = _MISSING) -> Any:
    """Read key from options first, then data, with optional default."""
    options = getattr(entry, "options", {})
    data = getattr(entry, "data", {})
    if default is _MISSING:
        return options.get(key, data.get(key))
    return options.get(key, data.get(key, default))


def iter_site_fuel_pairs(
    sites_data: dict[str, Any], chosen_fuels: Iterable[str]
) -> Iterator[tuple[str, str]]:
    """Yield (site_id, fuel_id) pairs for filtered station prices."""
    allowed_fuels = {str(fuel_id) for fuel_id in chosen_fuels}
    for site_id, site_data in sites_data.items():
        site_prices = site_data.get("prices", [])
        if not site_prices:
            continue
        for price_info in site_prices:
            fuel_id = str(price_info.get("FuelId"))
            if fuel_id in allowed_fuels:
                yield str(site_id), fuel_id


def remove_stale_registry_entities(
    hass: Any,
    entry: Any,
    active_unique_ids: set[str],
    unique_id_prefix: str,
) -> None:
    """Remove stale config-entry entities matching unique_id_prefix."""
    entity_registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        unique_id = getattr(registry_entry, "unique_id", None)
        if not unique_id or not unique_id.startswith(unique_id_prefix):
            continue
        if unique_id not in active_unique_ids:
            entity_registry.async_remove(registry_entry.entity_id)


def site_price_for_fuel(site_data: dict[str, Any], fuel_id: str) -> Any:
    """Return the matching fuel price value for a site, if available."""
    for price_info in site_data.get("prices", []):
        if str(price_info.get("FuelId")) == str(fuel_id):
            return price_info.get("Price")
    return None


def fuel_label_for_id(fuel_id: str) -> str:
    """Return friendly fuel label for a fuel id."""
    fuel_info = next(
        (item for item in FUEL_TYPES_OPTIONS if item["value"] == str(fuel_id)),
        {"label": str(fuel_id)},
    )
    return str(fuel_info["label"])


def resolve_location_from_input(
    hass: Any,
    user_input: dict[str, Any],
    errors: dict[str, str],
) -> tuple[float | None, float | None, str | None]:
    """Resolve coordinates from location entity first, then zone."""
    location_entity_id = user_input.get(LOCATION_ENTITY)
    if location_entity_id:
        location_state = hass.states.get(location_entity_id)
        if not location_state:
            errors[LOCATION_ENTITY] = "location_entity_not_found"
        else:
            lat, lon = coords_from_state(location_state)
            if lat is not None and lon is not None:
                return lat, lon, location_state.name
            errors[LOCATION_ENTITY] = "location_entity_missing_coordinates"

    zone_id = user_input.get(ZONE)
    zone_state = hass.states.get(zone_id)
    if not zone_state:
        errors[ZONE] = "zone_not_found"
        return None, None, None

    lat, lon = coords_from_state(zone_state)
    if lat is None or lon is None:
        errors[ZONE] = "zone_not_found"
        return None, None, None

    return lat, lon, zone_state.name
