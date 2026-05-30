import voluptuous as vol
from typing import Any
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE

from .const import (
    DOMAIN,
    ENABLE_GEO_ENTITIES,
    TOKEN,
    RADIUS,
    FUEL_TYPES,
    FUEL_TYPES_OPTIONS,
    LOCATION_ENTITY,
    ZONE,
)
from .coordinator import async_validate_token, QldFuelAuthError, QldFuelConnectionError
from .util import get_entry_value, resolve_location_from_input


def _location_entity_selector_options(hass: Any) -> list[dict[str, str]]:
    """Build dropdown options for entities that expose coordinates."""
    states = getattr(hass, "states", None)
    async_all = getattr(states, "async_all", None)
    if async_all is None:
        return []

    options: list[dict[str, str]] = []
    for state in async_all():
        entity_id = getattr(state, "entity_id", "")
        if not entity_id:
            continue

        domain = entity_id.split(".", 1)[0]
        if domain not in {"person", "device_tracker", "sensor"}:
            continue

        attrs = getattr(state, "attributes", {})
        if attrs.get("latitude") is None or attrs.get("longitude") is None:
            continue

        options.append({"value": entity_id, "label": state.name})

    return sorted(options, key=lambda item: item["label"].lower())


def _location_entity_selector(
    hass: Any, current_location_entity: str | None = None
) -> selector.SelectSelector:
    """Create a dropdown selector constrained to entities with coordinates."""
    options = _location_entity_selector_options(hass)
    option_values = {item["value"] for item in options}
    if current_location_entity and current_location_entity not in option_values:
        options.append({"value": current_location_entity, "label": current_location_entity})

    return selector.SelectSelector(
        selector.SelectSelectorConfig(options=options, mode="dropdown")
    )


class QldFuelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[misc,call-arg]
    VERSION = 1

    @staticmethod
    @callback  # type: ignore[untyped-decorator]
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return QldFuelOptionsFlowHandler(config_entry)

    @staticmethod
    def _build_location_unique_id(user_input: dict[str, Any], lat: float, lon: float) -> str:
        """Build a stable unique ID for this configured location."""
        location_entity_id = user_input.get(LOCATION_ENTITY)
        if location_entity_id:
            return f"location:{location_entity_id}"

        zone_id = user_input.get(ZONE)
        if zone_id:
            return f"zone:{zone_id}"

        return f"coords:{lat:.6f},{lon:.6f}"

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Handle the initial setup of an instance."""
        entries = self._async_current_entries()
        master_entry = next((e for e in entries if e.data.get("is_master")), None)
        errors: dict[str, str] = {}

        if user_input is not None:
            lat, lon, location_name = resolve_location_from_input(
                self.hass, user_input, errors
            )
            if lat is not None and lon is not None:
                await self.async_set_unique_id(self._build_location_unique_id(user_input, lat, lon))
                self._abort_if_unique_id_configured()
                user_input["is_master"] = not bool(master_entry)

                if master_entry:
                    user_input[TOKEN] = master_entry.data.get(TOKEN)
                else:
                    try:
                        await async_validate_token(self.hass, user_input.get(TOKEN))
                    except QldFuelAuthError:
                        errors["base"] = "invalid_auth"
                    except QldFuelConnectionError:
                        errors["base"] = "cannot_connect"

                if not errors:
                    user_input[CONF_LATITUDE] = lat
                    user_input[CONF_LONGITUDE] = lon

                    title = f"Fuel near {location_name}"
                    return self.async_create_entry(title=title, data=user_input)

        fields = {}
        if not master_entry:
            fields[vol.Required(TOKEN)] = str

        fields[vol.Optional(LOCATION_ENTITY)] = _location_entity_selector(self.hass)
        fields[vol.Required(ZONE, default="zone.home")] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="zone")
        )
        fields[vol.Required(RADIUS, default=5)] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="km")
        )
        fields[vol.Required(FUEL_TYPES, default=["12", "5", "3"])] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=FUEL_TYPES_OPTIONS, multiple=True)
        )
        fields[vol.Optional(ENABLE_GEO_ENTITIES, default=False)] = selector.BooleanSelector()

        return self.async_show_form(step_id="user", data_schema=vol.Schema(fields), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> config_entries.ConfigFlowResult:
        """Handle flow initiated by reauthentication."""
        self.context["entry_id"] = self._get_reauth_entry().entry_id
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Prompt for and validate a new subscriber token."""
        errors = {}
        if user_input is not None:
            token = user_input.get(TOKEN)
            try:
                await async_validate_token(self.hass, token)
            except QldFuelAuthError:
                errors["base"] = "invalid_auth"
            except QldFuelConnectionError:
                errors["base"] = "cannot_connect"
            else:
                entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={**entry.data, TOKEN: token},
                    )
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(TOKEN): str}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration of an existing entry."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        entries = self._async_current_entries()
        master_entry = next((e for e in entries if e.data.get("is_master")), None)
        is_master = entry and entry.data.get("is_master", False)
        errors: dict[str, str] = {}

        if user_input is not None:
            lat, lon, location_name = resolve_location_from_input(
                self.hass, user_input, errors
            )
            if lat is not None and lon is not None:
                updates = dict(user_input)
                updates["is_master"] = is_master
                if not is_master and master_entry:
                    updates[TOKEN] = master_entry.data.get(TOKEN)

                updates[CONF_LATITUDE] = lat
                updates[CONF_LONGITUDE] = lon

                return self.async_update_reload_and_abort(
                    entry,
                    title=f"Fuel near {location_name}",
                    data=updates,
                )

        data = entry.data if entry else {}
        options = entry.options if entry else {}

        fields = {}
        if is_master:
            fields[vol.Required(TOKEN, default=data.get(TOKEN, ""))] = str

        current_location_entity = options.get(LOCATION_ENTITY, data.get(LOCATION_ENTITY))
        location_entity_key = vol.Optional(LOCATION_ENTITY)
        if current_location_entity:
            location_entity_key = vol.Optional(LOCATION_ENTITY, default=current_location_entity)
        fields[location_entity_key] = _location_entity_selector(self.hass, current_location_entity)
        current_zone = options.get(ZONE, data.get(ZONE, "zone.home"))
        fields[vol.Required(ZONE, default=current_zone)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="zone")
        )
        fields[vol.Required(RADIUS, default=options.get(RADIUS, data.get(RADIUS, 5)))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="km")
        )
        fields[vol.Required(FUEL_TYPES, default=options.get(FUEL_TYPES, data.get(FUEL_TYPES, ["12", "5", "3"])))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=FUEL_TYPES_OPTIONS, multiple=True)
        )
        fields[
            vol.Optional(
                ENABLE_GEO_ENTITIES,
                default=options.get(ENABLE_GEO_ENTITIES, data.get(ENABLE_GEO_ENTITIES, False)),
            )
        ] = selector.BooleanSelector()

        return self.async_show_form(step_id="reconfigure", data_schema=vol.Schema(fields), errors=errors)


class QldFuelOptionsFlowHandler(config_entries.OptionsFlow):  # type: ignore[misc]
    """Handle options flow for QLD Service Station Prices."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage zone, radius, and fuel type options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            lat, lon, _ = resolve_location_from_input(self.hass, user_input, errors)
            if lat is not None and lon is not None:
                user_input[CONF_LATITUDE] = lat
                user_input[CONF_LONGITUDE] = lon
                return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data

        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=vol.Schema({
                (
                    vol.Optional(LOCATION_ENTITY, default=options.get(LOCATION_ENTITY, data.get(LOCATION_ENTITY)))
                    if options.get(LOCATION_ENTITY, data.get(LOCATION_ENTITY))
                    else vol.Optional(LOCATION_ENTITY)
                ): _location_entity_selector(
                    self.hass, options.get(LOCATION_ENTITY, data.get(LOCATION_ENTITY))
                ),
                vol.Required(ZONE, default=options.get(ZONE, data.get(ZONE, "zone.home"))): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="zone")
                ),
                vol.Required(RADIUS, default=options.get(RADIUS, data.get(RADIUS, 5))): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="km")
                ),
                vol.Required(FUEL_TYPES, default=options.get(FUEL_TYPES, data.get(FUEL_TYPES, ["12", "5", "3"]))): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=FUEL_TYPES_OPTIONS, multiple=True)
                ),
                vol.Optional(
                    ENABLE_GEO_ENTITIES,
                    default=options.get(ENABLE_GEO_ENTITIES, data.get(ENABLE_GEO_ENTITIES, False)),
                ): selector.BooleanSelector(),
            })
        )