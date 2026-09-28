"""Mestske lazne Nove Mesto na Morave integration."""

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .coordinator import LazneCoordinator, occupancy_coordinator, schedule_coordinator

PLATFORMS = (Platform.SENSOR, Platform.BINARY_SENSOR)


@dataclass
class LazneRuntimeData:
    occupancy: LazneCoordinator
    schedule: LazneCoordinator
    cancel_clock: CALLBACK_TYPE


type LazneConfigEntry = ConfigEntry[LazneRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: LazneConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    occupancy = occupancy_coordinator(hass, session, entry)
    schedule = schedule_coordinator(hass, session, entry)
    await asyncio.gather(occupancy.async_refresh(), schedule.async_refresh())

    @callback
    def update_time_dependent_entities(_now: object) -> None:
        schedule.async_update_listeners()

    cancel_clock = async_track_time_interval(
        hass, update_time_dependent_entities, timedelta(minutes=1)
    )
    entry.runtime_data = LazneRuntimeData(occupancy, schedule, cancel_clock)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LazneConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data.cancel_clock()
    return unload_ok
