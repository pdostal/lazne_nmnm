"""Sensors for Mestske lazne NMnM."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import LazneEntity
from .parser import is_open, select_schedule


@dataclass(frozen=True, kw_only=True)
class OccupancyDescription(SensorEntityDescription):
    area: str


OCCUPANCY_SENSORS = tuple(
    OccupancyDescription(
        key=area,
        translation_key=area,
        area=area,
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
    )
    for area in (
        "areal",
        "bazen",
        "fitness",
        "wellness",
        "koupele",
        "masaze",
        "solarium",
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    data = entry.runtime_data
    async_add_entities(
        [
            OccupancySensor(data.occupancy, entry, description)
            for description in OCCUPANCY_SENSORS
        ]
        + [SaunaSensor(data.schedule, entry)]
    )


class OccupancySensor(LazneEntity, SensorEntity):
    entity_description: OccupancyDescription

    def __init__(
        self, coordinator, entry: ConfigEntry, description: OccupancyDescription
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> int | None:
        return (
            self.coordinator.data.get(self.entity_description.area)
            if self.coordinator.data
            else None
        )


class SaunaSensor(LazneEntity, SensorEntity):
    _attr_translation_key = "sauna"
    _attr_icon = "mdi:sauna"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "sauna")

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        now = dt_util.now()
        day = select_schedule(self.coordinator.data, now.date()).days[now.weekday()]
        return next(
            (slot.sauna_type for slot in day.wellness if is_open((slot,), now.time())),
            "zavřeno",
        )
