"""Opening-hours sensors for Mestske lazne NMnM."""

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import LazneEntity
from .parser import is_open, select_schedule


@dataclass(frozen=True, kw_only=True)
class OpeningDescription(BinarySensorEntityDescription):
    schedule_key: str


OPENING_SENSORS = tuple(
    OpeningDescription(
        key=f"{key}_open",
        translation_key=f"{key}_open",
        schedule_key=key,
        icon="mdi:clock-outline",
    )
    for key in ("pool", "fitness", "wellness")
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        [
            OpeningSensor(entry.runtime_data.schedule, entry, description)
            for description in OPENING_SENSORS
        ]
    )


class OpeningSensor(LazneEntity, BinarySensorEntity):
    entity_description: OpeningDescription

    def __init__(
        self, coordinator, entry: ConfigEntry, description: OpeningDescription
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    def _today(self):
        now = dt_util.now()
        if not self.coordinator.data:
            return now, None
        return now, select_schedule(self.coordinator.data, now.date()).days[
            now.weekday()
        ]

    @property
    def is_on(self) -> bool:
        now, day = self._today()
        if day is None:
            return False
        return is_open(getattr(day, self.entity_description.schedule_key), now.time())

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        _, day = self._today()
        if day is None:
            return {}
        return {
            "hours_today": getattr(day, f"raw_{self.entity_description.schedule_key}")
        }
