"""Per-station fuel price sensors."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.recorder import history, get_instance
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .sensor_common import device_info_for_entry
from .util import fuel_label_for_id, site_price_for_fuel

_LOGGER = logging.getLogger(__name__)


class FuelPriceSensor(CoordinatorEntity, SensorEntity):  # type: ignore[misc]
    """Representation of a specific station's Fuel Price Sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "¢/L"
    _attr_device_class = None
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: Any, site_id: str, fuel_id: str) -> None:
        super().__init__(coordinator)
        self.site_id = site_id
        self.fuel_id = fuel_id
        self._attr_translation_key = "station_fuel_price"

        self._14d_low: float | None = None
        self._14d_low_days: int | None = None
        self._14d_avg: float | None = None
        self._7d_low: float | None = None
        self._7d_low_days: int | None = None
        self._7d_avg: float | None = None

        site = coordinator.data.get("sites", {}).get(site_id)
        site_name = site["name"] if site else "Unknown"

        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry.entry_id}_{fuel_id}_{site_id}"
        self._attr_translation_placeholders = {
            "station": site_name,
            "fuel_type": fuel_label_for_id(fuel_id),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return device_info_for_entry(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        site_data = self.coordinator.data.get("sites", {}).get(self.site_id, {})
        value = site_price_for_fuel(site_data, self.fuel_id)
        return float(value) if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        site = self.coordinator.data.get("sites", {}).get(self.site_id, {})
        stats = site.get("stats", {}).get(self.fuel_id, {})

        attrs = {
            "address": f"{site.get('address')} {site.get('postcode')}".strip(),
            "latitude": site.get("latitude"),
            "longitude": site.get("longitude"),
            "distance": f"{site.get('distance')} km",
            "fuel_id": self.fuel_id,
            "difference_to_qld_cheapest": stats.get("qld_delta", 0),
        }
        if site.get("latitude") is not None and site.get("longitude") is not None:
            attrs["Location"] = f"{site.get('latitude')}, {site.get('longitude')}"

        if self._7d_low is not None:
            attrs.update({
                "7_day_low": f"{self._7d_low} ¢/L",
                "7_day_average": f"{self._7d_avg} ¢/L",
                "days_since_7_day_low": f"{self._7d_low_days} days",
            })
        if self._14d_low is not None:
            attrs.update({
                "14_day_low": f"{self._14d_low} ¢/L",
                "14_day_average": f"{self._14d_avg} ¢/L",
                "days_since_14_day_low": f"{self._14d_low_days} days",
            })
        return attrs

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._update_history()

    def _handle_coordinator_update(self) -> None:
        site = self.coordinator.data.get("sites", {}).get(self.site_id)
        site_name = site["name"] if site else "Unknown"
        self._attr_translation_placeholders = {
            "station": site_name,
            "fuel_type": fuel_label_for_id(self.fuel_id),
        }
        self.hass.async_create_task(self._update_history())
        super()._handle_coordinator_update()

    async def _update_history(self) -> None:
        """Query the recorder for historical lows and averages."""
        if self.hass.is_stopping:
            return

        now = dt_util.utcnow()
        start_time = now - timedelta(days=14)

        try:
            state_history = await get_instance(self.hass).async_add_executor_job(
                history.get_significant_states, self.hass, start_time, None, [self.entity_id]
            )
        except (AttributeError, ValueError) as err:
            _LOGGER.debug("Could not retrieve history for %s: %s", self.entity_id, err)
            self.async_write_ha_state()
            return

        if self.entity_id in state_history:
            valid_points = []
            for s in state_history[self.entity_id]:
                if s.state in ("unknown", "unavailable", "", None):
                    continue
                try:
                    valid_points.append((float(s.state), s.last_changed))
                except ValueError:
                    continue

            if valid_points:
                min_price = min(p[0] for p in valid_points)
                min_time = max(p[1] for p in valid_points if p[0] == min_price)

                self._14d_low = min_price
                self._14d_low_days = (now - min_time).days
                self._14d_avg = round(sum(p[0] for p in valid_points) / len(valid_points), 1)

                seven_days_ago = now - timedelta(days=7)
                recent_points = [p for p in valid_points if p[1] > seven_days_ago]

                if recent_points:
                    min_7d = min(p[0] for p in recent_points)
                    min_7d_time = max(p[1] for p in recent_points if p[0] == min_7d)
                    self._7d_low = min_7d
                    self._7d_low_days = (now - min_7d_time).days
                    self._7d_avg = round(sum(p[0] for p in recent_points) / len(recent_points), 1)

        self.async_write_ha_state()
