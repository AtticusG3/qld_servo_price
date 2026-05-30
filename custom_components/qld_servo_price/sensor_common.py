"""Shared helpers for sensor platform modules."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN, LOCATION_ENTITY
from .util import get_entry_value

try:
    from homeassistant.core import HomeAssistant
except ImportError:  # pragma: no cover
    HomeAssistant = Any

try:
    from homeassistant.config_entries import ConfigEntry
except ImportError:  # pragma: no cover
    ConfigEntry = Any


def get_fuel_data(
    data_dict: dict[str, dict[str, Any]] | None, f_id: str
) -> dict[str, Any] | None:
    """Helper to find fuel data by string fuel ID."""
    if not data_dict:
        return None
    return data_dict.get(str(f_id))


def find_all_tracked_best(
    hass: HomeAssistant, fuel_id: str
) -> tuple[float | None, dict[str, Any] | None]:
    """Return the cheapest local price and its station data across all tracked zones."""
    best_price = None
    best_station = None
    for entry in hass.config_entries.async_entries(DOMAIN):
        coord = entry.runtime_data
        if getattr(coord, "data", None):
            local_best = get_fuel_data(coord.data.get("local_cheapest"), fuel_id)
            if local_best and local_best.get("price") is not None:
                price = float(local_best["price"])
                if best_price is None or price < best_price:
                    best_price = price
                    best_station = local_best
    return best_price, best_station


def resolve_location_source(entry: ConfigEntry) -> str | None:
    """Return the configured location source entity for derived nearby sensors."""
    value = get_entry_value(entry, LOCATION_ENTITY)
    return value if isinstance(value, str) else None


def device_info_for_entry(entry: ConfigEntry) -> DeviceInfo:
    """Return DeviceInfo for a config entry's local zone monitor."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"zone_{entry.entry_id}")},
        name=entry.title,
        manufacturer="Queensland fuel price API",
        model="Local Zone Monitor",
        entry_type=DeviceEntryType.SERVICE,
    )


def device_info_statewide() -> DeviceInfo:
    """Return DeviceInfo for statewide aggregate sensors."""
    return DeviceInfo(
        identifiers={(DOMAIN, "qld_statewide_global")},
        name="QLD statewide prices",
        manufacturer="Queensland fuel price API",
        model="Statewide monitor",
        entry_type=DeviceEntryType.SERVICE,
    )


def station_site_attrs(
    coordinator_data: dict[str, Any],
    site_id: str | None,
    station_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build best-price station attrs from processed coordinator site data."""
    if site_id is None:
        return {"status": "Price found but site_id is missing"}

    site = coordinator_data.get("sites", {}).get(str(site_id))
    if not site and station_data:
        site = {
            "name": station_data.get("name"),
            "address": station_data.get("address"),
            "postcode": station_data.get("postcode"),
            "latitude": station_data.get("latitude"),
            "longitude": station_data.get("longitude"),
            "distance": None,
        }
    if not site:
        return {"status": f"Site {site_id} not found in raw data"}

    s_lat = site.get("latitude")
    s_lon = site.get("longitude")
    dist_km: str | float = site.get("distance", "N/A")
    if dist_km is None:
        dist_km = "N/A"

    attrs: dict[str, Any] = {
        "station_name": site.get("name") or "Unknown",
        "address": f"{site.get('address', '')} {site.get('postcode', '')}".strip(),
        "latitude": s_lat,
        "longitude": s_lon,
        "distance_km": dist_km,
    }
    if s_lat is not None and s_lon is not None:
        attrs["Location"] = f"{s_lat}, {s_lon}"
    return attrs
