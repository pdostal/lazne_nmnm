"""Shared entity helpers."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LazneCoordinator


class LazneEntity(CoordinatorEntity[LazneCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LazneCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Městské lázně Nové Město na Moravě",
            manufacturer="Nové Město na Moravě",
            configuration_url="https://lazne.nmnm.cz/",
        )
